
import argparse
import json
import time
import uuid
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_SAMPLE_TEXT = "SampleData123"


def make_driver(chromedriver_path: str = "chromedriver", headless: bool = False, window_size: str = "1280,900"):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={window_size}")
    # Basic safety/compat
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # If caller requests 'auto' chromedriver, try to use webdriver-manager to install a matching driver
    if chromedriver_path == 'auto':
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except Exception:
            # fallback to given path if webdriver-manager isn't available
            service = Service('chromedriver')
    else:
        service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def element_metadata(el) -> Dict[str, Any]:
    try:
        tag = el.tag_name
    except Exception:
        tag = None
    attrs = {}
    for a in ["type", "id", "name", "class", "placeholder", "required", "aria-label", "value", "title"]:
        try:
            attrs[a] = el.get_attribute(a)
        except Exception:
            attrs[a] = None

    text = None
    try:
        text = el.text.strip()
    except Exception:
        text = None

    try:
        xpath = el.get_attribute('xpath')
    except Exception:
        xpath = None

    return {
        "tag": tag,
        "text": text,
        "attributes": attrs,
    }


def build_locator_candidate(el) -> tuple:
    """Return a locator tuple (By.<XXX>, value) preferring id, then name, then aria-label, then placeholder, then CSS."""
    try:
        el_id = el.get_attribute('id')
        if el_id:
            return ('By.ID', el_id)
        name = el.get_attribute('name')
        if name:
            return ('By.NAME', name)
        aria = el.get_attribute('aria-label')
        if aria:
            return ('By.XPATH', f"//*[normalize-space(@aria-label)='{aria}']")
        placeholder = el.get_attribute('placeholder')
        if placeholder:
            return ('By.XPATH', f"//*[normalize-space(@placeholder)='{placeholder}']")
        # Try classes and tag
        tag = el.tag_name
        classes = el.get_attribute('class') or ''
        if classes.strip():
            first_class = classes.split()[0]
            return ('By.CSS_SELECTOR', f"{tag}.{first_class}")
        # Fallback to tag
        return ('By.TAG_NAME', tag)
    except Exception:
        return ('By.TAG_NAME', el.tag_name if hasattr(el, 'tag_name') else 'unknown')


def format_code_line(locator_tuple, meta: Dict[str, Any]) -> str:
    by, val = locator_tuple
    # Escape single quotes in val
    safe_val = val.replace("'", "\\'") if isinstance(val, str) else str(val)
    comment_parts = []
    a = meta.get('attributes', {})
    if a.get('type'):
        comment_parts.append(f"type={a.get('type')}")
    if a.get('placeholder'):
        comment_parts.append(f"placeholder={a.get('placeholder')}")
    if a.get('required'):
        comment_parts.append('required')
    comment = '  # ' + ', '.join(comment_parts) if comment_parts else ''
    return f"driver.find_element({by}, '{safe_val}'){comment}"


def safe_type(el, sample: str) -> Dict[str, Any]:
    """Type into input/textarea elements if possible."""
    log = {"action": "type", "success": False, "error": None}
    try:
        el.clear()
    except Exception:
        pass
    try:
        el.send_keys(sample)
        log["success"] = True
    except Exception as e:
        log["error"] = str(e)
    return log


def safe_click(el) -> Dict[str, Any]:
    log = {"action": "click", "success": False, "error": None}
    try:
        el.click()
        log["success"] = True
    except ElementClickInterceptedException as e:
        log["error"] = f"intercepted: {e}"
    except Exception as e:
        log["error"] = str(e)
    return log


def analyze_page(driver, allow_submit: bool = False, sample_text: str = DEFAULT_SAMPLE_TEXT, pause: float = 0.3) -> Dict[str, Any]:
    results = {
        "scan_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "elements": [],
        "interactions": [],
    }

    # Wait a short while for dynamic content
    time.sleep(1)

    # Inputs and textareas
    inputs = driver.find_elements(By.TAG_NAME, "input")
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    selects = driver.find_elements(By.TAG_NAME, "select")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    anchors = driver.find_elements(By.TAG_NAME, "a")

    # Process inputs
    for el in inputs:
        meta = element_metadata(el)
        results["elements"].append(meta)
        it_log = {"element": meta, "attempts": []}
        t = (meta["attributes"].get("type") or "text").lower()
        # Only attempt safe interactions for common text-like fields or toggles
        if t in ["text", "email", "tel", "password", "search", "url"]:
            it = safe_type(el, sample_text)
            it_log["attempts"].append(it)
            results["interactions"].append(it_log)
        elif t in ["checkbox", "radio"]:
            it = safe_click(el)
            it_log["attempts"].append(it)
            results["interactions"].append(it_log)
        else:
            # ignore file/hidden/submit by default
            if t == "submit" and allow_submit:
                it = safe_click(el)
                it_log["attempts"].append(it)
                results["interactions"].append(it_log)
        time.sleep(pause)

    # Textareas
    for el in textareas:
        meta = element_metadata(el)
        results["elements"].append(meta)
        it_log = {"element": meta, "attempts": []}
        it = safe_type(el, sample_text)
        it_log["attempts"].append(it)
        results["interactions"].append(it_log)
        time.sleep(pause)

    # Selects
    for el in selects:
        meta = element_metadata(el)
        # gather options
        try:
            opts = [o.text for o in el.find_elements(By.TAG_NAME, 'option')]
        except Exception:
            opts = []
        meta["attributes"]["options"] = opts
        results["elements"].append(meta)
        it_log = {"element": meta, "attempts": []}
        try:
            sel = Select(el)
            if len(opts) > 1:
                sel.select_by_index(1)
                it_log["attempts"].append({"action": "select", "index": 1, "option": opts[1], "success": True})
            else:
                it_log["attempts"].append({"action": "select", "success": False, "reason": "no non-default option"})
        except Exception as e:
            it_log["attempts"].append({"action": "select", "success": False, "error": str(e)})
        results["interactions"].append(it_log)
        time.sleep(pause)

    # Buttons
    for el in buttons:
        meta = element_metadata(el)
        results["elements"].append(meta)
        it_log = {"element": meta, "attempts": []}
        button_type = (meta["attributes"].get("type") or "").lower()
        # avoid clicking non-safe buttons unless allow_submit
        if button_type == "submit" and allow_submit:
            it = safe_click(el)
            it_log["attempts"].append(it)
            results["interactions"].append(it_log)
        else:
            # just record presence
            it_log["attempts"].append({"action": "record", "success": True})
            results["interactions"].append(it_log)
        time.sleep(pause)

    # Anchors (links)
    for el in anchors:
        meta = element_metadata(el)
        href = meta["attributes"].get("value") or el.get_attribute("href")
        meta["attributes"]["href"] = href
        results["elements"].append(meta)
        results["interactions"].append({"element": meta, "attempts": [{"action": "record_link", "href": href}]})

    return results


def main():
    parser = argparse.ArgumentParser(description="Frontend analyzer: scans a webpage for form elements and logs interactions")
    parser.add_argument("--url", required=True, help="Target URL to analyze")
    parser.add_argument("--chromedriver", default="chromedriver", help="Path to chromedriver executable")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--output", default="frontend_report.json", help="Output file")
    parser.add_argument("--format", choices=["json", "code"], default="code", help="Output format: json or code-style locators")
    parser.add_argument("--allow-submit", action="store_true", help="Allow clicking submit buttons (DANGEROUS)")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE_TEXT, help="Sample text to type into inputs")
    args = parser.parse_args()

    driver = None
    try:
        driver = make_driver(chromedriver_path=args.chromedriver, headless=args.headless)
        print(f"[INFO] Opening {args.url}")
        driver.get(args.url)
        # wait until some content loads (title or body)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except Exception:
            pass

        time.sleep(1)
        results = analyze_page(driver, allow_submit=args.allow_submit, sample_text=args.sample)
        results["url"] = args.url
        results["title"] = driver.title
        # Write results in requested format
        if args.format == 'json':
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Scan complete. JSON results written to {args.output}")
        else:
            # code-style output: create locator lines
            code_lines: List[str] = []
            recorded = set()
            for item in results.get('elements', []):
                # We don't have direct element handle here; use attributes to reconstruct a pseudo-locator
                attrs = item.get('attributes', {})
                # make a fake minimal meta with attributes for formatting
                meta = {'attributes': attrs}
                # prefer id/name/aria/placeholder/class/tag
                if attrs.get('id'):
                    locator = ('By.ID', attrs.get('id'))
                elif attrs.get('name'):
                    locator = ('By.NAME', attrs.get('name'))
                elif attrs.get('aria-label'):
                    locator = ('By.XPATH', f"//*[normalize-space(@aria-label)='{attrs.get('aria-label')}']")
                elif attrs.get('placeholder'):
                    locator = ('By.XPATH', f"//*[normalize-space(@placeholder)='{attrs.get('placeholder')}']")
                elif attrs.get('class'):
                    first_class = (attrs.get('class') or '').split()[0]
                    tag = item.get('tag') or 'input'
                    locator = ('By.CSS_SELECTOR', f"{tag}.{first_class}")
                else:
                    locator = ('By.TAG_NAME', item.get('tag') or 'input')

                line = format_code_line(locator, item)
                # Avoid duplicates
                if line not in recorded:
                    code_lines.append(line)
                    recorded.add(line)

            with open(args.output, 'w', encoding='utf-8') as f:
                f.write('\n'.join(code_lines) + '\n')

            print(f"[INFO] Scan complete. Code-style results written to {args.output}")
    except WebDriverException as e:
        print(f"[ERROR] WebDriver error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == '__main__':
    main()

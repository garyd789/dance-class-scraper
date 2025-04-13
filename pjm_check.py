from playwright.sync_api import sync_playwright

def main():
    url = "https://www.versd.co/profile/pjm"
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so you can see it
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Navigating to {url} ...")
        try:
            response = page.goto(url, timeout=30000)
            
            if response and response.ok:
                print("Successfully accessed the site!")
            else:
                print("Failed to access the site or received a non-OK response.")
            
            print("Final URL:", page.url)
            
            # Take a screenshot and save it as pjm_checl.png
            page.screenshot(path="pjm_checl.png")
            print("Screenshot saved as pjm_checl.png")
            
            # Wait for user input before closing the browser
            input("Press Enter to close the browser window...")
        except Exception as e:
            print("An error occurred while navigating to the site:", e)
            input("Press Enter to close the browser window...")
        finally:
            browser.close()

if __name__ == "__main__":
    main()

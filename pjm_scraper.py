from playwright.sync_api import sync_playwright
import json
import traceback

def main():
    url = "https://www.versd.co/profile/pjm"
    
    with sync_playwright() as p:
        # Launch the browser in non-headless mode so you can see the process.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Navigating to PJM Dance NYC website...")
            response = page.goto(url, timeout=30000)
            print("Page loaded successfully")
            
            # Verify that we are on the correct page
            print(f"Current URL: {page.url}")
            page.screenshot(path="initial_page.png")
            print("Screenshot saved as 'initial_page.png'")
            
            # Check if we are on a Cloudflare challenge page
            if "challenge" in page.url or page.query_selector("#challenge-error-text"):
                print("Detected Cloudflare challenge page. Waiting for it to resolve...")
                try:
                    page.wait_for_url("**/pjm", timeout=30000)
                    print("Cloudflare challenge resolved successfully!")
                except Exception as e:
                    print(f"Cloudflare challenge not resolved within timeout: {e}")
                    print("Current page content:")
                    print(page.content())
                    page.screenshot(path="cloudflare_challenge.png")
                    print("Screenshot of challenge page saved as 'cloudflare_challenge.png'")
                    raise Exception("Failed to bypass Cloudflare security")
            
            # Wait for the schedule table to appear
            print("Looking for schedule table...")
            page.wait_for_selector("td[role='gridcell']")
            print("Schedule table found!")
            page.screenshot(path="pjm_schedule_table.png")
            print("Screenshot of schedule table saved as 'pjm_schedule_table.png'")
            
            # Extract the date (here statically set, adjust selector if dynamic)
            print("\nExtracting date")
            date_text = "April 10"
            print(f"Date is {date_text}")
            
            # Extract all class elements
            print("\nExtracting class elements...")
            class_elements = page.query_selector_all("td[role='gridcell'][style*='width: 100%'] > div > div")
            print(f"Found {len(class_elements)} day elements")
            
            # Create a list to store all class data
            all_class_data = []
            
            # Loop through each class element and extract data
            for i, class_element in enumerate(class_elements):
                print(f"\nProcessing class {i + 1} of {len(class_elements)}...")
                
                # Initialize class data dictionary
                class_data = {
                    "date": date_text,
                    "time": "",
                    "name": "",
                    "staff": "",
                    "room": "",
                    "instructor": "",
                    "instructor_bio": "",
                    "description": ""
                }
                
                # Extract class time
                time_element = class_element.query_selector("div > div > :nth-child(4)")
                if time_element:
                    class_data["time"] = time_element.inner_text().strip()
                    print(f"    Time: {class_data['time']}")
                
                # Extract class name
                name_element = class_element.query_selector("div > div > a")
                if name_element:
                    class_data["name"] = name_element.inner_text().strip()
                    print(f"    Name: {class_data['name']}")
                
                # Extract instructor name
                instructor_element = class_element.query_selector("div > div > :nth-child(2)")
                if instructor_element:
                    class_data["instructor"] = instructor_element.inner_text().strip()
                    class_data["staff"] = instructor_element.inner_text().strip()
                    print(f"    Instructor: {class_data['instructor']}")

                # Extract description
                description_element = class_element.query_selector("div > div > :nth-child(3)")
                if description_element:
                    class_data["description"] = description_element.inner_text().strip()
                    print(f"    Music: {class_data['description']}")       

                # Add extracted data to our list
                all_class_data.append(class_data)
            
            # Print a summary of the extracted data
            print("\nSummary of extracted data:")
            print("-" * 30)
            print(f"Total days: {len(class_elements)}")
            print(f"Total classes: {len(all_class_data)}")
            
            # Save the extracted data to a JSON file
            print("\nSaving data to pjm_classes.json...")
            with open("pjm_classes.json", "w", encoding="utf-8") as f:
                json.dump(all_class_data, f, indent=2, ensure_ascii=False)
            print("Data saved to pjm_classes.json")
            
            # Print a sample of the data
            print("\nSample of extracted data:")
            print("-" * 30)
            if all_class_data:
                sample = all_class_data[0]
                for key, value in sample.items():
                    print(f"{key}: {value}")
            
            # Take a final screenshot called pjm_chek.png
            page.screenshot(path="pjm_check.png")
            print("Screenshot of the final page saved as 'pjm_check.png'")
            
            # Wait for user input before closing the browser
            input("Press Enter to close the browser window...")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
            input("Press Enter to close the browser window...")
        finally:
            browser.close()
            print("Browser closed successfully")

if __name__ == "__main__":
    main()

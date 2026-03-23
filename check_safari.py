from selenium import webdriver
import time

def test_safari():
    print("Attempting to launch Safari...")
    try:
        driver = webdriver.Safari()
        print("SUCCESS! Safari launched.")
        print("Navigate to Google...")
        driver.get("https://www.google.com")
        time.sleep(2)
        print("Closing Safari...")
        driver.quit()
        print("Test Passed.")
    except Exception as e:
        print("\n!!! FAILED TO LAUNCH SAFARI !!!")
        print(f"Error: {e}")
        print("\nSOLUTION:")
        print("1. Open Safari")
        print("2. In top menu: Safari > Settings > Advanced")
        print("3. Check 'Show features for web developers' (or 'Show Develop menu')")
        print("4. Close Settings")
        print("5. In top menu: Click 'Develop' -> Click 'Allow Remote Automation'")
        print("6. Try running this script again.")

if __name__ == "__main__":
    test_safari()

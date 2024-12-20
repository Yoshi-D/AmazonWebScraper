from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv

# Set up Selenium WebDriver
driverPath = "/Users/shamdhage/Desktop/brave-chromedriver-mac-x64/chromedriver" # Path to ChromeDriver
service = Service(driverPath)
options = webdriver.ChromeOptions()
options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
options.add_argument("--headless")
options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" # Path to Brave Browser (this is the default)
driver = webdriver.Chrome(service=service, options= options)


def random_delay(min_delay=0.8, max_delay=2.0): #creates random delays to mimic human behaviour
    delay = random.uniform(min_delay, max_delay)
    time.sleep(0.3)
    time.sleep(delay)
def scroll_to_load_all_elements(): #scroll to bottom of the page to load all the elements
    previous_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_delay()
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == previous_height:
            print("All elements loaded.")
            break

        previous_height = new_height
def scrape_best_sellers(category_url, category_name): #main function to scrape a bestseller

    print(f"Scraping category: {category_name}")
    try:
        driver = webdriver.Chrome(service=service, options= options)
        driver.get(category_url)
        time.sleep(3)
    except Exception as e:
        print(f"Error opening url for {category_name}: {e}")
        return

    products = []
    for page in range(1, 21):
        try:
            print(f"Scraping page {page} of {category_name}...")
            scroll_to_load_all_elements()

            product_elements = driver.find_elements(By.ID, "gridItemRoot") #all product have same class names
            print(f"Number of products on this page are: {len(product_elements)}")
            random_delay()

            for index,product in enumerate(product_elements):
                try:
                    id = product.find_element(By.XPATH,f'//*[@id="p13n-asin-index-{index}"]/div').get_attribute('data-asin')
                    product_link = product.find_element(By.XPATH,f'//*[@id="{id}"]/div/div/a').get_attribute("href")
                    print("Product link is:" ,product_link)

                    name = product.find_element(By.XPATH, f'//*[@id="{id}"]/div/div/a/span/div').text
                    print(f"Opened {name} in a new tab")

                    driver.execute_script("window.open(arguments[0]);", product_link)
                    driver.switch_to.window(driver.window_handles[1])
                    random_delay()

                    price = driver.find_element(By.XPATH, '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[3]/span[2]/span[2]').text
                    print(f"The price is {price}")

                    discount = (driver.find_element(By.XPATH, '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]').text)[1:]
                    print(f"The discount is {discount}")

                    rating = driver.find_element(By.XPATH, '//*[@id="acrPopover"]/span[1]/a/span').text
                    print(f"The rating is {rating}")

                    try:
                        ship_from = driver.find_element(By.XPATH, '//*[@id="tabular-buybox"]/div[1]/div[4]/div/span').text
                        print(f"Shipped from {ship_from}")
                    except:
                        ship_from = "N/A"

                    sold_by = driver.find_element(By.XPATH,'//*[@id="tabular-buybox"]/div[1]/div[6]/div/span').text
                    print(f"Sold by {sold_by}")

                    try:
                        description = driver.find_element(By.XPATH, '//*[@id="feature-bullets"]/ul').text
                        print("Got description")
                        random_delay()
                    except:
                        description = "N/A"
                        print("Description not available")

                    try:
                        number_bought = driver.find_element(By.XPATH, '//*[@id="social-proofing-faceout-title-tk_bought"]/span[1]').text.replace('bought','')
                        print(f"Number of people who bought: {number_bought}")
                    except:
                        number_bought = "N/A"

                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, "ul.a-unordered-list li img")
                        image_urls = []

                        for image in images:
                            image_url = image.get_attribute("src")
                            if image_url[-3:] != 'gif' and '360' not in image_url and 'play' not in image_url and 'amazon-avatars' not in image_url:
                                image_urls.append(image_url)
                        print(f"Scraped {len(image_urls)} images")

                    except Exception as e:
                        image_urls = "N/A"
                        print("Images are not scraped: ",e)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])


                    if int(discount.strip('%')) > 50 : #discount filter
                        products.append({
                            "Product Name": name,
                            "Product Price": price,
                            "Sale Discount": discount,
                            "Best Seller Ranking": index+1,
                            "Ship From": ship_from,
                            "Sold By": sold_by,
                            "Rating": rating,
                            "Product Description": description,
                            "Number Bought in the Past Month": number_bought,
                            "Category Name": category_name,
                            "All Available Images": image_urls
                        })
                    random_delay()
                except Exception as e:
                    print(f"Error scraping product: {e}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

            # Go to the next page
            next_button = driver.find_element(By.PARTIAL_LINK_TEXT, 'Next')
            driver.execute_script("arguments[0].click();", next_button)
            print("Next page button clicked")
            random_delay()

        except Exception as e:

            print(f"Error on page {page}: {e}")
            break

    print(f"Scraped {len(products)} products from {category_name}.")
    return products


def save_to_csv(data, filename="amazon_best_sellers.csv"):

    keys = data[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as file:
        dict_writer = csv.DictWriter(file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Data saved to {filename}.")



try:

    categories = [ #this is a list of different bestseller categories, can change this to different categories
        {"name": "Home & Kitchen", "url": "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0"},
        {"name":"Baby Products","url":"https://www.amazon.in/gp/bestsellers/baby/ref=zg_bs_nav_baby_0"},
        {"name":"Bags, Wallets and Luggage","url":"https://www.amazon.in/gp/bestsellers/luggage/ref=zg_bs_nav_luggage_0"},
        {"name":"Books","url":'https://www.amazon.in/gp/bestsellers/books/ref=zg_bs_nav_books_0'},
        {"name":"Car & Motorbike","url":'https://www.amazon.in/gp/bestsellers/automotive/ref=zg_bs_nav_automotive_0'},
        {"name":"Clothing & Accessories","url":'https://www.amazon.in/gp/bestsellers/apparel/ref=zg_bs_nav_apparel_0'},
        {"name":"Computers & Accessories","url":"https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0"},
        {"name":"Electronics","url":"https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0"},
        {"name":"Garden & Outdoors","url":"https://www.amazon.in/gp/bestsellers/garden/ref=zg_bs_nav_garden_0"},
        {"name":"Health & Personal Care","url":"https://www.amazon.in/gp/bestsellers/hpc/ref=zg_bs_nav_hpc_0"},
    ]

    all_products = []
    for category in categories:
        products = scrape_best_sellers(category["url"], category["name"])
        all_products.extend(products)

    if all_products:
        save_to_csv(all_products) #saves the data to the csv file
finally:
    driver.quit()

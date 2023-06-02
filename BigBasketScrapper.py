from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep


class Scraper:

    def __init__(self, url):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument(f'user_agent={user_agent}')
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(url)
        self.wait = WebDriverWait(self.driver, 10)
        self.data = {}

    def scrape(self):
        self.scrape_category_subcategory_product()
        self.scrape_sku_id()
        self.scrape_image()
        self.scrape_brand()
        self.scrape_sku_name_and_size()
        self.scrape_mrp_and_selling_price()
        self.scrape_out_of_stock()
        self.scrape_product_rating()
        self.scrape_total_ratings_and_reviews()
        self.scrape_reviews()
        print(self.data)

    def scrape_category_subcategory_product(self):
        div_category = self.driver.find_element(By.CSS_SELECTOR, "div._3moNK")
        a_tags = div_category.find_elements(By.CSS_SELECTOR, "a._3WUR_._3bj9B.rippleEffect")[1:]
        category, sub_category, product = [a_tag.text.replace(">", "").strip() for a_tag in a_tags]
        self.data["Category"] = category
        self.data["Sub-Category"] = sub_category
        self.data["Product"] = product

    def scrape_sku_id(self):
        self.data["SKU ID"] = self.driver.current_url.split("/")[-3]

    def scrape_image(self):
        image_div = self.driver.find_element(By.CSS_SELECTOR, "div._2FbOx")
        image = image_div.find_element(By.CSS_SELECTOR, "img._3oKVV").get_attribute("src")
        self.data["Image"] = image

    def scrape_brand(self):
        brand_div = self.driver.find_element(By.CSS_SELECTOR, "div._2yfKw")
        brand = brand_div.find_element(By.CSS_SELECTOR, "a._2zLWN._3bj9B.rippleEffect").text
        self.data["Brand"] = brand

    def scrape_sku_name_and_size(self):
        sku_div = self.driver.find_element(By.CSS_SELECTOR, "div._2yfKw")
        sku_string = sku_div.find_element(By.CSS_SELECTOR, "h1.GrE04").text
        sku_name = sku_string.split(" - ")[0].strip()
        sku_size = sku_string.split(",")[-1].strip()
        self.data["SKU Name"] = sku_name
        self.data["SKU Size"] = sku_size

    def scrape_mrp_and_selling_price(self):
        price_div = self.driver.find_element(By.CSS_SELECTOR, "div#price")
        try:
            mrp_element = price_div.find_element(By.CSS_SELECTOR, "td._2ifWF")
            mrp = mrp_element.text
        except NoSuchElementException:
            mrp = "NA"
        selling_price_element = price_div.find_element(By.CSS_SELECTOR, "td.IyLvo")
        selling_price = selling_price_element.text
        self.data["MRP"] = mrp
        self.data["Selling Price"] = selling_price

    def scrape_out_of_stock(self):
        try:
            self.driver.find_element(By.CSS_SELECTOR, "div._36qqs")
            in_stock = "No"
        except NoSuchElementException:
            in_stock = "Yes"
        out_of_stock = "Yes" if in_stock == "No" else "No"
        self.data["In Stock"] = in_stock
        self.data["Out of Stock"] = out_of_stock

    def scrape_product_rating(self):
        try:
            product_rating_element = self.driver.find_element(By.CSS_SELECTOR, "div._2Ze34")
            product_rating = product_rating_element.text
        except (NoSuchElementException, TimeoutException):
            product_rating = "NA"
        self.data["Product Rating"] = product_rating

    def scrape_total_ratings_and_reviews(self):
        try:
            review_div = self.driver.find_element(By.CSS_SELECTOR, "div._1AXTE")
            reviews_element = review_div.find_element(By.CSS_SELECTOR, "span[style='color: rgb(74, 74, 74); position: relative; top: 1px;']")
            total_reviews_ratings = reviews_element.text
        except NoSuchElementException:
            total_reviews_ratings = "NA"

        if total_reviews_ratings != "NA":
            total_ratings, total_reviews = total_reviews_ratings.split('&')
            total_ratings = total_ratings.strip()[:-8]
            total_reviews = total_reviews.strip()[:-8]
        else:
            total_ratings = total_reviews = "NA"
        self.data["Total Ratings"] = total_ratings
        self.data["Total Reviews"] = total_reviews

    def scrape_reviews(self):
        try:
            reviews_link_element = self.driver.find_element(By.CSS_SELECTOR, "a._1xG1d")
            reviews_link = reviews_link_element.get_attribute('href')
            self.driver.get(reviews_link)

            actions = ActionChains(self.driver)
            old_scroll_height = 0

            while True:
                actions.send_keys(Keys.END).perform()
                sleep(5)
                new_scroll_height = self.driver.execute_script("return document.documentElement.scrollHeight")

                if new_scroll_height == old_scroll_height:
                    break
                else:
                    old_scroll_height = new_scroll_height

            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.zF-ya")
            reviews = [review_element.text for review_element in review_elements]
        except NoSuchElementException:
            reviews = []
        self.data["Reviews"] = reviews


if __name__ == '__main__':
    url = "https://www.bigbasket.com/pd/1204455/fortune-sunflower-refined-oil-sun-lite-3x910-g/?nc=l3category&t_pg=L3Categories&t_p=l3category&t_s=l3category&t_pos=3&t_ch=desktop"
    scraper = Scraper(url)
    scraper.scrape()

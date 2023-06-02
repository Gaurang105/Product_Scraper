# Importing nescessary libraries
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
import dateparser
import re
from random import randint
#import helperFunctions

class MyntraScrapper():
    def __init__(self):
        self.driver = None
        self.marketPlaceID = "PF"
        self.marketPlace = "Myntra"
        self.marketPlaceURL = None
        self.marketPlaceRegion = "IN"
    
    def openWindow(self, link):
        chrome_options = Options()
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get(link)
        
        self.driver.implicitly_wait(3)
        print("Page loaded successfully")
        
    def closeWindow(self):
        self.driver.quit()
    
    def getOverallRating(self):
        try:
            overall = self.driver.find_element(By.XPATH,"//div[@class='index-flexRow index-averageRating']").find_element(By.TAG_NAME,"span").text.strip()
        except NoSuchElementException:
            overall = ""
        return overall
    
    def goToReviews(self):
        try:
            button = self.driver.find_element(By.XPATH,"//div[@class='detailed-reviews-flexReviews']").find_element(By.TAG_NAME,"a").get_attribute("href")
            self.driver.get(button)
            time.sleep(2)
        except NoSuchElementException:
            pass
    
    def clickDropdown(self):
        try:
            wait = WebDriverWait(self.driver, 10) 
            dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='dropdown-filter-dropdownFilterContainer']")))
            dropdown.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

    
    def getRatingsCount(self,productUrl):
        common_class = self.driver.find_element(By.XPATH,"//div[@class='index-flexRow index-margin22']")
        d = {"ra_5" : 0, "ra_4" : 0, "ra_3" : 0, "ra_2" : 0, "ra_1" : 0}
        allElements = common_class.find_elements(By.XPATH,"//div[@class='index-flexRow index-ratingBarContainer']")
        for ele in allElements:
            ratingCount = ele.find_element(By.TAG_NAME,"progress").get_attribute("data-rating").strip()
            d[f"ra_{ratingCount}"] = ele.find_element(By.CLASS_NAME,"index-count").text.strip()
        return d
    
    def clickRating(self,i):
        try:    
            self.clickDropdown()
            self.driver.find_element(By.XPATH,"//div[@class='dropdown-filter-dropdown dropdown-filter-open']").find_element(By.XPATH,"//div[@class='dropdown-filter-item'][{}]".format(i)).click()
        except NoSuchElementException:
            self.clickDropdown()
            dropdown = self.driver.find_element(By.XPATH,"//div[@class='dropdown-filter-dropdown dropdown-filter-open']")
            dropdown.find_element(By.XPATH,"//div[@class='dropdown-filter-item'][{}]".format(i)).click()
        
    def scrollTillEnd(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            for scrollVal in range(1000, 1601, 200):
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight-{scrollVal});")
                time.sleep(0.5)
            time.sleep(randint(1,2))
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def extractReviews(self, reviewUrl, method = 'all'):
        """
        Extracts the product reviews from the specified URL and returns the extracted data.
        """
        reviewlist = []
        flag = 0
        reviews=self.driver.find_element(By.XPATH,"//div[@class='detailed-reviews-userReviewsContainer']").find_elements(By.XPATH,"//div[@class='user-review-userReviewWrapper ']")
        for rev in reviews:
            try:
                star = rev.find_element(By.XPATH,"//div[@class='user-review-main user-review-showRating']").text.strip().split()[0]
            except:
                star = ""
            try:
                if len(rev.text.strip().split("\n"))>3:
                    review = rev.text.strip().split("\n")[1]
                else:
                    review = ""
            except:
                review = ""
            try:
                if len(rev.text.strip().split("\n"))>3:
                    name_date = rev.text.split("\n")[2]
                else:
                    name_date = rev.text.split("\n")[1]
                index = name_date.index(re.findall(r"\d",name_date)[0])
                name = name_date[:index]
                date = name_date[index:]
                date = dateparser.parse(date).date()
            except:
                continue
            record = {
                'ReviewerName': name,
                'Date': date,
                'ReviewTitle': "",
                'Rating': star,
                'Review': review
            }
            try:
                if (date.today() - date).days >= method:
                    flag = 1
                    break
                else:
                    reviewlist.append(record)
            except:
                reviewlist.append(record)
        self.driver.execute_script("window.scrollTo(0, 0);")
        return reviewlist
 
    def getReviewsByDate(self, productUrl, productCount, startDate, endDate, last_ReviewID):
        self.openWindow(productUrl)    
        """Go to the reviews page,
        Sort the reviews according to most recent,
        
        """
        self.goToReviews()
        self.clickRating(1) # 1 for most_recent ones
        allReviews = []
        for i in range(2,7):
            self.clickRating(i)
            time.sleep(0.5)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                recordList=[]
                for scrollVal in range(1000, 1601, 200):
                    self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight-{scrollVal});")
                    time.sleep(0.5)
                time.sleep(randint(3,4))
                self.flag = False
                reviews = self.extractReviews(productUrl)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                for rev in reviews:
                    if rev["Date"] > dateparser.parse(startDate).date() and rev["Date"] <= dateparser.parse(endDate).date():
                        recordList.append(rev)
                    elif rev["Date"] <= dateparser.parse(startDate).date():    
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        self.flag = True
                        break
                if self.flag==True:
                    break
                if new_height == last_height:
                    break
                last_height = new_height
            allReviews.extend(recordList)
            self.driver.execute_script("window.scrollTo(0, 0);")
        df = pd.DataFrame.from_dict(allReviews, orient='columns')
        
        # Review -> not null or not an empty string
        df = df[~(df['Review'].isnull()) & (df['Review'].str.len() > 0)]

        # Rating -> Fill na with 0 and convert to int
        df['Rating'] = df['Rating'].fillna(value=0)
        df['Rating'] = df['Rating'].apply(pd.to_numeric)

        # ReviewerName -> convert to str
        df['ReviewerName'] = df['ReviewerName'].astype(str)

        df["ReviewID"] = [f"{last_ReviewID.split('R')[0]}R{str(i)}" for i in range(int(last_ReviewID.split('R')[1]) + 1, int(last_ReviewID.split('R')[1]) + df.shape[0] + 1)]
        df["Date"] = df["Date"].apply(lambda x: dateparser.parse(x).date())
        df["MarketPlace"] = self.marketPlace
        df["Region"] = self.marketPlaceRegion

        df['JsonData'] = ""

        selectCols = ['Date', 'ReviewID', 'ReviewTitle', 'Review',
                      'Rating', 'ReviewerName', 'MarketPlace', 'Region', 'JsonData']
        df = df[selectCols]

        recordList = df.to_dict('records')
        return recordList
    
    def getProductInfo(self, productUrl):
        self.openWindow(productUrl)
        
        try:
            brand_name = self.driver.find_element(By.XPATH,"//h1[@class='pdp-title']").text.strip()
        except:
            brand_name=""
        try:
            prodName = self.driver.find_element(By.XPATH,"//h1[@class='pdp-name']").text.strip()
        except:
            prodName=""
        try:
            img_url=[]
            imgLinks = self.driver.find_element(By.XPATH,"//div[@class='image-grid-container common-clearfix']").find_elements(By.CLASS_NAME,'image-grid-image')
            for img in imgLinks:
                img_url.append(img.get_attribute("style").split('\"')[1].split('\"')[0])
        except:
            img_url=[]
        try:
            price = self.driver.find_element(By.XPATH,"//span[@class='pdp-price']").text.strip()
        except:
            price = ""
        try:
            rating = self.getOverallRating()
        except:
            rating=0
        try:
            noOfReviews = self.driver.find_element(By.XPATH,"//div[@class='detailed-reviews-headline']").text.strip().split("(")[1].split(")")[0]
        except:
            noOfReviews = 0
        return {"BrandName":brand_name,"ProductName":prodName,"AvgRating":rating,"ReviewsCount": noOfReviews, "Likes": "", "Size": "",
                "Quantity": "", "Cost": price, "ImageLinks": img_url
                }
        
    def getReviews(self, productUrl, productCount, method = 'all'):
        self.openWindow(productUrl)    
        """Go to the reviews page,
        Sort the reviews according to most recent,
        
        """
        self.goToReviews()
        self.clickRating(1) # 1 for most_recent ones
        allReviews = []
        for i in range(2,7):
            self.clickRating(i)
            time.sleep(0.5)
            self.scrollTillEnd()
            allReviews.extend(self.extractReviews(productUrl, method))
        df = pd.DataFrame.from_dict(allReviews, orient='columns')
        
        # Review -> not null or not an empty string
        df = df[~(df['Review'].isnull()) & (df['Review'].str.len() > 0)]
        # Rating -> Fill na with 0 and convert to int
        df['Rating'] = df['Rating'].fillna(value=0)
        df['Rating'] = df['Rating'].apply(pd.to_numeric)

        # ReviewerName -> convert to str
        df['ReviewerName'] = df['ReviewerName'].astype(str)

        df["ReviewID"] = [
            f"{self.marketPlaceID}{self.marketPlaceRegion}{str(productCount)}R{str(i)}" for i in range(1, df.shape[0]+1)]
        print(df)
        df["Date"] = df["Date"].apply(lambda x: dateparser.parse(str(x)).date())
        df["MarketPlace"] = self.marketPlace
        df["Region"] = self.marketPlaceRegion

        df['JsonData'] = ""

        selectCols = ['Date', 'ReviewID', 'ReviewTitle', 'Review',
                      'Rating', 'ReviewerName', 'MarketPlace', 'Region', 'JsonData']
        df = df[selectCols]

        recordList = df.to_dict('records')
        # helperFunctions.sendStatus(token, json.dumps(
            # {'type': 'terminal', 'message': 'Total reviews - {i}'.format(i = len(recordList))}))
        print(f"Total reviews - {len(recordList)}")
        return recordList
    
    def scrapAndSaveRatings(self, productUrl, Product_ID):
        ratings = self.getRatingsCount(productUrl)
        merged_df = {}
        for i in ratings.keys():
            merged_df[i] = ratings[i]
        reviewsCount = {"re_1":0,"re_2":0,"re_3":0,"re_4":0,"re_5":0}
        for i in reviewsCount.keys():
            merged_df[i] = reviewsCount[i]
        avg_rating = self.getOverallRating()
        merged_df["Average Rating"]=avg_rating
        df = pd.DataFrame(merged_df, index = [0])
        df['Product_id'] = Product_ID
        return df.to_dict('records')
        
url = "https://www.myntra.com/dresses/antheaa/antheaa-fuchsia-solid-chiffon-smocked-tiered-midi-dress/15577328/buy"
obj = MyntraScrapper()
ab = obj.getReviews(url,7,30)
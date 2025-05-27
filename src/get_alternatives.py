from google import genai
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import time
import dotenv
import logging
import requests

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.use_DB import DBConnection

#API key used for Gemini services --> .env
dotenv.load_dotenv() 
API_KEY = os.getenv("API_KEY")
logger = logging.getLogger(__name__)

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
    "port": int(os.environ.get('MYSQL_PORT', 3306))  # Ensure port is included and cast to int
} 

class GenerateAlternatives(DBConnection):
    def __init_(self, website_url, data_transfer, db_config=CONFIG, key=API_KEY, user_id=None):
        self.url = website_url
        self.client = genai.Client(key)
        self.user_id = user_id
        self.db_config = db_config
        self.data_transfer = data_transfer

        self.domains = [".com", ".org", ".net", ".io", ".co", ".be", ".uk", ".de", ".fr", ".jp", ".au", ".ca", ".it", ".es", ".ru", ".ch", ".nl", ".se", ".no", ".fi", ".dk"]

        try: 
            filename = "src/green-urls.csv"
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File {filename} not found.")
            self.green_df = pd.read_csv(filename)
        except FileNotFoundError as e:
            logger.info("Error while loading green URLs", e)
            raise
        super().__init__("websites")

    def calculate_total_emissions(self, green_hosted=None, data_transfer=None) -> float:
        """Using the data transfer and green hosting metric from the users current webiste, return a total carbon footprint by taking global estiamtes of intensities on different segments and summing them out
        Args:
            data_transfer (float): data transfer in bytes from the website
            green_hosted (bool): highlights whether or not the hosting of a wbsite is eco-friendly or not. Defaults to False.

        Returns:
            float: _description_
        """
        #TODO - Calculate carbon footprint
        if data_transfer is None:
            data_transfer = self.data_transfer
        data_transfer_gb = self.data_transfer / (1024 * 1024 * 1024) 

        # Global averages for energy intensity on different segments
        energy_intensity_datacenter = 0.055
        energy_intensity_network = 0.059
        energy_intensity_device = 0.080

        # globl average for crbon intensity bsed on whether or not the hosting is green/eco-frendly
        if green_hosted is None:
            green_hosted = self.green_hosted
        carbon_intensity = 50 if self.green_hosted else 494

        # calcualte total emissions for each segment based on the data transfer from the website
        emissions_datacenter = data_transfer_gb * energy_intensity_datacenter * carbon_intensity
        emisions_network = data_transfer_gb * energy_intensity_network * carbon_intensity
        emissions_device = data_transfer_gb * energy_intensity_device * carbon_intensity

        # sum out all segments to get the total emissions gathered
        total_emissions = emissions_datacenter + emisions_network + emissions_device

        logger.info(f"Total emissions calculated: {total_emissions} kg CO2e for {data_transfer_gb} GB of data transfer")
        return total_emissions
    
    def fetch_matches(self):
        """This function is designed to return the row in which a user's current website was found. If the website was not found yet, 
        it will call call the ai_response which will make suggestions and store it in the database

        Retuns:
            list: row the current website was found
        """
        select_value = "*"
        where_values = ["userID", "url"]
        values = [self.user_id, self.url]
        self.open()
        rows = self.select_items(select_value, where_values, values, fetchAmount=1)
        self.close()

        logger.info(f"Rows fetched for user {self.user_id} and URL {self.url}: {rows}")
        if not rows:
            self.fetch_ai_response()
    def store_website(self, suggestions):
        """Writes the website data into the SQL database for the respective user. This data will be used to quick-fetch suggestions for the user's current website
        --> reduces digital footprint/carbon emissions

        Args:
            url (string): path to the website
            suggestions (list): list of alternative websites previously found to be more eco-friendly
            date (string): date the website was written to the database --> used to determine how old the data is
        """
        data_transfer = self.calculate_total_emissions()
        where_values = ["userID"]
        values = [self.user_id, self.url, data_transfer, suggestions[0], suggestions[1], suggestions[2]]
        self.insert_items(where_values, values)

    def is_green(self, url):
        """Determines of the current URL exists in the gren URL database. Idf it does,
        return true, otherwise false. This is used to calcualte the total carbon footprint of the given website

        Args:
            url (string): URL of the current website to be checked

        Returns:
            bool: True if the website is green hosted, false otherwise
        """
        if url in self.green_df["url"].values:
            return True
        else:   
            return False

    def filter_suggestions(self, suggestions):
        """takes a list of AI generated urls that were suggested and filters them out based on their 
        overall carbon footprint. The function will need to pass through a JS function that will need to calculate the 
        total data transfer of the current suggestion so that we can accurately calculate. 

        Args:
            suggestions (list): list of suggested website alternatives generated from AI API

        Returns:
            list: Pruned list of suggestions based on the best results
        """
        scores = []
        dt_api = "htttp://localhost:3000/FUNCTION"
        for suggestion in suggestions:
            for domain in self.domains:
                if domain in suggestion:
                    url = suggestion[:suggestion.rfind(domain) + 4]

                if url:
                    green = self.is_green(url)
                    params = {"url": url}
                    response = requests.get(dt_api, params=params)
                    data = response.json()
                    data_transfer = data["transfer"]
                    score = self.calculate_total_emissions(green, data_transfer)
                    scores.append((suggestion, score))
        
        sort_scores = [i for i in sorted(scores, key=lambda x: x[1])]
        return sort_scores[:3]
    

    def fetch_ai_response(self):
        """This function is designed to generate a list of suggested websites that are similar to the user's current website ONLY IF they have not bee nfound in the current local database and passes the given conditions for search.
        After the suggested have been generated, they will be passed to the frontend service and written to the database.

        Returns: 
            list: set of suggested websites that are similar to the user's current website
        """
        prompt = f"Generate an exact count of 8 alternative websites that are very similar in terms of content category to this provided website: {self.url}. Verify that the websites you generate match the overall message and content. Avoid any unnecessary text."
        date = time.strftime("%Y-%m-%d")
        try:
            response = self.client.generate(prompt=prompt)
            tokens = response.split(" ")

            suggestions = []
            for token in tokens:
                for domain in self.domains:
                    if domain in token:
                        suggestions.append(token)

            self.store_website(suggestions, date)
        except Exception as e:
            logger.info("Error while generating AI response", e)

        if suggestions:
            filtered_suggestions = self.filter_suggestions(suggestions)
            return filtered_suggestions
        else:
            return None
    
    def fetch_light_suggestions(self, warning):
        suggestion = ""
        if warning == "long":
            suggestion = "Looks like you've been active for a while, try taking a break!"
        elif warning == "video":
            suggestion = "Looks like the video is really long, try watching a shorter one!"
        elif warning == "message":
            suggestion = "Looks like you've been chatting for quite some time, try taking a break!"

        return suggestion
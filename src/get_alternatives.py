from google import genai
from codecarbon import EmissionsTracker
import mysql.connector
from mysql.connector import Error
import os
import json
import time
import dotenv
import logging

#API key used for Gemini services --> .env
env = dotenv.load_dotenv() 
API_KEY = env["API_KEY"]
tracker = EmissionsTracker()
logger = logging.getLogger(__name__)

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies!'),
    "database": os.environ.get('MYSQL_DATABASE', 'website_tracker')
}

class GenerateAlternatives:
    def __init_(self, website_url, data_transfer, green_hosted, db_config=CONFIG, key=API_KEY, user_id=None):
        self.url = website_url
        self.client = genai.Client(key)
        self.user_id = user_id
        self.db_config = db_config
        self.data_transfer = data_transfer
        self.green_hosted = green_hosted

        try:
            self.connection = mysql.connector.connect(
                host = self.db_config["host"],
                user = self.db_config["user"],
                password = self.db_config["password"],
                database = self.db_config["database"]
            )
            self.cursor = self.connection.cursor()
        except Error as e:
            logger.info("Error while connecting to MySQL", e)
        
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS websites (id INT AUTO_INCREMENT PRIMARY KEY, url VARCHAR(255), data_transfer INT, web_suggested_1 VARCHAR(255), web_suggested_2 VARCHAR(255), web_suggested_3 VARCHAR(255), date VARCHAR(255))")
        
    def calculate_total_emissions(self) -> float:
        """Using the data transfer and green hosting metric from the users current webiste, return a total carbon footprint by taking global estiamtes of intensities on different segments and summing them out
        Args:
            data_transfer (float): data transfer in bytes from the website
            green_hosted (bool): highlights whether or not the hosting of a wbsite is eco-friendly or not. Defaults to False.

        Returns:
            float: _description_
        """
        #TODO - Calculate carbon footprint
        data_transfer_gb = self.data_transfer / (1024 * 1024 * 1024) 

        # Global averages for energy intensity on different segments
        energy_intensity_datacenter = 0.055
        energy_intensity_network = 0.059
        energy_intensity_device = 0.080

        # globl average for crbon intensity bsed on whether or not the hosting is green/eco-frendly
        carbon_intensity = 50 if self.green_hosted else 494

        # calcualte total emissions for each segment based on the data transfer from the website
        emissions_datacenter = data_transfer_gb * energy_intensity_datacenter * carbon_intensity
        emisions_network = data_transfer_gb * energy_intensity_network * carbon_intensity
        emissions_device = data_transfer_gb * energy_intensity_device * carbon_intensity

        # sum out all segments to get the total emissions gathered
        total_emissions = emissions_datacenter + emisions_network + emissions_device
        return total_emissions
    
    def store_website(self, suggestions, date):
        """Writes the website data into the SQL database for the respective user. This data will be used to quick-fetch suggestions for the user's current website
        --> reduces digital footprint/carbon emissions

        Args:
            url (string): path to the website
            suggestions (list): list of alternative websites previously found to be more eco-friendly
            date (string): date the website was written to the database --> used to determine how old the data is
        """
        data_transfer = self.calculate_total_emissions()
        sql = "INSERT INTO websites (id, url, data_transfer, web_suggested_1, web_suggested_2, web_suggested_3, date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (self.user_id, self.url, data_transfer, suggestions[0], suggestions[1], suggestions[2], date)
        self.cursor.execute(sql, val)
        self.connection.commit()

    def fetch_ai_response(self):
        """This function is designed to generate a list of suggested websites taht are similar to the user's current website ONLY IF they have not bee nfound in the current local database and passes the given conditions for search.
        After the suggested have been generated, they will be passed to the frontend service and written to the database.

        Returns:
            list: set of suggested websites that are similar to the user's current website
        """
        prompt = f"Generate an exact count of 5 alternative websites that are very close in similarity to this provided website: {self.url}. Verify that the websites you generate match the overall message and content. Avoid any unnecessary text."
        date = time.strftime("%Y-%m-%d")
        try:
            response = self.client.generate(prompt=prompt)
            tokens = response.split(" ")

            suggestions = []
            for token in tokens:
                if ".com" in token:
                    suggestions.append(token)
            self.store_website(suggestions, date)
        except Exception as e:
            logger.info("Error while generating AI response", e)

        if suggestions:
            return suggestions
        else:
            return None
from google import genai
import os
import json
import time
import dotenv

#API key used for Gemini services --> .env
env = dotenv.load_dotenv() 
API_KEY = env["API_KEY"]

class GenerateAlternatives:
    def __init_(self, website_url, key=API_KEY, filename="src/site_data/sites_visited.json", user_id=None):
        self.url = website_url
        self.client = genai.Client(key)
        self.user_id = user_id
        self.filename = filename
        
        # Ensure the user_id folder exists in the site_data directory
        user_folder = os.path.join("src/site_data", self.user_id)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        if not os.path.exists(os.path.join(self.user_id, self.filename)): # if the data file does not exist for the user,create it
            with open(os.path.join(self.user_id, self.filename), "w") as f:
                json.dump({}, f)
        

        
    def calculate_total_emissions(self, data_transfer, green_hosted=False) -> float:
        """Using the data transfer and green hosting metric from the users current webiste, return a total carbon footprint by taking global estiamtes of intensities on different segments and summing them out
        Args:
            data_transfer (float): data transfer in bytes from the website
            green_hosted (bool): highlights whether or not the hosting of a wbsite is eco-friendly or not. Defaults to False.

        Returns:
            float: _description_
        """
        #TODO - Calculate carbon footprint
        data_transfer_gb = data_transfer / (1024 * 1024 * 1024) 

        # Global averages for energy intensity on different segments
        energy_intensity_datacenter = 0.055
        energy_intensity_network = 0.059
        energy_intensity_device = 0.080

        # globl average for crbon intensity bsed on whether or not the hosting is green/eco-frendly
        carbon_intensity = 50 if green_hosted else 494

        # calcualte total emissions for each segment based on the data transfer from the website
        emissions_datacenter = data_transfer_gb * energy_intensity_datacenter * carbon_intensity
        emisions_network = data_transfer_gb * energy_intensity_network * carbon_intensity
        emissions_device = data_transfer_gb * energy_intensity_device * carbon_intensity

        # sum out all segments to get the total emissions gathered
        total_emissions = emissions_datacenter + emisions_network + emissions_device
        return total_emissions
    
    def store_website(self, url, suggestions, date):
        """Writes the website data into the json database for the respective user. This data will be used to quick-fetch suggestions for the user's current website
        --> reduces digital footprint/carbon emissions

        Args:
            url (string): path to the website
            suggestions (list): list of alternative websites previously found to be more eco-friendly
            date (string): date the website was written to the database --> used to determine how old the data is
        """
        route = os.path.join(self.user_id, self.filename)
        with open(route, "r") as f:
            data = json.load(f)

        if url not in data:
            data[url] = {
                "suggestions": suggestions,
                "date": date
            }

        with open(route, "w") as f:
            json.dump(data, f, indent=4)

    def fetch_suggestions(self, url):
        """attempts to fetch any data that has already been fund from the user's current website, if a quick-fetch is not found, 
        it will run the API function to fetch suggestions(Increases digital footprint/carbon emissions)

        Args:
            url (string): path to the website

        Returns:
            list: List of suggested websites that are more eco-friendly
        """
        route = os.path.join(self.user_id, self.filename)
        with open(route, "r") as f:
            data = json.load(f)

        if url in data:
            suggestions = data[url]["suggestions"]
        else:
            suggestions = self.fetch_response(url)

        return suggestions
    
    def fetch_response(self, url):
        return 
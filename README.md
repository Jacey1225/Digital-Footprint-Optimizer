CarbonBytes: Digital Carbon Footprint Tracker
Overview
CarbonBytes is a browser extension that helps users track, understand, and reduce their digital carbon footprint. By monitoring online activities and suggesting eco-friendly alternatives, this tool empowers users to make environmentally conscious choices while browsing the web.
The Problem
Digital activities carry a significant environmental cost that often goes unnoticed:

The internet consumes approximately 1021 TWh/year of electricity
In 2022, the US emitted 6.343 billion metric tons of CO2 equivalent
Digital data growth is accelerating faster than sustainability measures can address
Common online activities produce substantial carbon emissions:

Google Search: 0.2g CO2e per search (3.85g with typical browsing behavior)
AI-Powered Search: 4.14g CO2e per response
Video Streaming: 0.42 kg CO2e per hour



Our Solution
CarbonBytes tracks your digital activities in real-time and provides actionable recommendations to reduce your carbon footprint:

Activity Monitoring: Tracks web browsing, search queries, video streaming, and AI interactions
Carbon Calculations: Uses established emission factors to calculate your digital carbon footprint
Smart Recommendations: Suggests lower-carbon alternatives like:

Reduced video resolution when appropriate
Less data-intensive websites for similar content
More efficient AI query strategies


Weekly Reports: Provides visual analytics of your digital carbon impact and savings

Technical Implementation
Back-End

Gemini API integration for smart recommendations
Carbon footprint calculation engine
Activity data collection and processing
Alternative content suggestion system
JSON-based activity logging for weekly reports

Front-End

User activity tracking
Notification system for real-time recommendations
Data visualization for carbon impact statistics
Intuitive browser extension interface

Impact
By making small changes to daily digital habits, users can collectively make a significant environmental impact. CarbonBytes helps bridge the gap between digital convenience and environmental responsibility.
Installation
[Coming soon - Installation instructions will be added upon release]
Contributing
We welcome contributions to help improve CarbonBytes! Please see our CONTRIBUTING.md for details on how to get involved.
License
This project is licensed under the MIT License - see the LICENSE.md file for details.
Acknowledgments

The Green Web Foundation for CO2 calculation methodologies
OECD-OPSI research on digital carbon footprints
All contributors and supporters of sustainable computing initiatives

Data Processing Optimization Method:
Front-End: 
1. For each hour of the day, track user activity and divide the total minutes the user was active by 60 to get the percentage of activity for that hour. 
2. At the end of the day, send the full 24-hour report to the back-end API
It should look like this ([0, 0, 0, 0.2, 0.3, 0, 0.5, 0.8, 0.8, 0.76, 0.3, 0.21, 0, 0.05, 0.01, 0.09, 0, 0, 0.5, 0.8, 0.8, 0.76, 0.3, 0.1]) This is an example of a list of percentage of activity for each hour of the day
3. After this report is sent to the back-end API, it will process it to identify spikes within the hours such as index 7 with an activity percentage of 0.8. 
This process is determined using standard deviations, and will output a seperate list of each respective index such as [7, 19, etc...] 
4. As more data fills up each day, it will begin to cluster patterns together using the k-means clustering algorithm, modifying the pattern in-place ignoring uncommon outliers. 
5. When this final result is made, it will attach the known pattern of hours to a database given the current day of the week. This will help the model generalize over each day of the week as data grows more abundant.
6. Keeping records of the previous activity reports from each day, it will ignore data that seems unusual to its known patterns, and as they get more consistent, it will pick up where it left and adjust itself accordingly. 
The final result of the pattern output is each index that the user is most active such as [7, 19, etc...] which can be called from the front-end API to let it know exactly what time frames to start watching activity, and when not to. 
## Webscraping example

This repository and the tasks below exemplify a general recipe for scraping any website that has nicely-structured data, by copying cURL commands for http requests, and caching http response data locally. Follow this recipe to get a feel for how to access data from APIs that don't come with a manual.

## RYM data analysis

The RUN script of this python repository will download all the pages in a rateyourmusic top chart of your choosing, and do some rudimentary processing of the data in the `"object_release"` cards on the pages. Top charts on RYM typically have 125 or 126 pages of 40 cards each, totalling 5000 or 5040 cards.

# CAUTION

It is highly recommended that you only scrape RYM (and glitchwave) through a VPN connection. The Sonemic, Inc. firewall is more ban-happy against bots than is the average website. There is a safeguard in the API module of this repository that will abort mission at a single non-okay http response code, and another safeguard that will exit the script if the saved cookies and headers are more than 60 minutes old. Hopefully these safeguards will make it so you only get a captcha check and not an IP ban when the RYM firewall gets suspicious. But if you do get an IP ban, it would be better if it were a VPN server's IP and not your home IP.

## Instructions

1. Install python requirements:
- https://pypi.org/project/bs4/
- https://pypi.org/project/requests/

2. Clone this repository.

3. In your CLI, navigate to the directory above this repository. You will execute the script with the directory above this repository as your working directory.

4. In the directory above this repository, create a directory named `_auth` and add a file named `rateyourmusic_auth.py` to the `_auth` directory. It will be imported by the API module of this repository.

5. Connect to your VPN.

6. Open a private browsing session of your browser. In the private browsing session, visit rateyourmusic.com so that site cookies populate in the browsing session.
  
7. If your VPN server is already blocked by RYM, then close the private browsing tab, disconnect from your VPN, and start again from step 5. with a different server on your VPN network. Try connecting to a few different servers on your VPN network until you find one that isn't blocked.
  
8. Open the developer tools of the private browser tab before proceeding (typically by pressing F12).

9. Navigate to a main link for a rateyourmusic top chart. An example main link to a top chart is given in the RUN script of this repository, commented out to start with. Either un-comment the main link in the RUN script now and use it for the remaining steps, or replace it with the other main link of your choosing.

10. Now that you have loaded a main page of a top chart, navigate to the network monitor of the open developer tools in your browser tab. It should have recorded all the http requests of the browsing session (if not, refresh the page). Hover your mouse on the "Name" of the first http request. A tooltip should appear with a url. The url should match the main link you chose for the top chart.

11. Right click on the first http request and click Copy > Copy as cURL (bash)

12. Visit https://curlconverter.com/

13. Paste the cURL (bash) command into the field on the curl converter website. Python code should populate right below where you pasted your command.

14. In the python code that populated, highlight the entirety of the `cookies` and `headers` variable declarations. Copy the code and paste it into your rateyourmusic_auth.py file that you made in step 4. Save the file.

15. You are now ready to start scraping a RYM top chart and processing the scraped data. As per step 9, make sure your chosen main link to a top chart is un-commented in or pasted in to the RUN script. In your CLI, navigate to the directory above this cloned repository, and run the following command:

```
python -m rateyourmusic.run_scraper
```

16. In your CLI you should see messages giving feedback that individual chart pages are being downloaded, and it will print `"object_release"` card data from the pages as they come in. The individual chart pages will save locally to a `_data` directory, cached for future runs of the same script.

Happy coding!

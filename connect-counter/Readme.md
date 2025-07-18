Axon Fusus Community Camera Scraper

This Python script scrapes public camera statistics (Registered and Integrated) from a list of Axon Fusus community program landing pages, such as [Connect Chicopee](https://connectchicopee.org) or [NYC Connect](https://newyorkcityconnect.org/), among others, and saves the results to a csv file.  

You can use the plain python script -- camcount.py with a list of sites you want to check as urls.txt. Prefereable for long lists, or running as a cron job. 

Or you can use app-count.py which is the same thing bbut with a graphical user inteface. -- easier to use, little to no computer skills needed. Just paste the urls you want to check in the box as one or a list. 

usage:
```
python camcount.py
```
or 
```
python app.py
```


Both save the output to csv. Saves to csv the following: number of reported registered_cameras, number of reported integrated_cameras, datae  + time, url

If you have python and all the dependencies installed, all you need to do is save your preferred version and run it. Otherwise you need python, as well as playwright. 

Playwright might seem like overkill to get two numbers from a website, but the numbers only appear after some javascript shenangigans on the connect websites, so this is the best soloution I could figure out. 

To install the Playwright library open a terminal and eneter
    
```
    pip install playwright
```
and then 

```
playwright install
```
   <img width="490" height="427" alt="image" src="https://github.com/user-attachments/assets/9f83a92e-3944-454d-ac64-4da42639dc33" />

Webscraper that uses bs4 to download a list of flock transparency portals. 

To run, download the contents of this folder, and make sure you have all python depencies installesd by opening a ternminal and running 

```
pip install requests beautifulsoup4 lxml
```

 The script transparency-portal-checker.py will attempt to do the following for each url in a file named urls.csv in the same directory:
 - save the raw html contetn
 - if any .pdf, .csv, .xlsx or .zip files are found linked from the page, it also downloads these.
 - Saves each page's contents in a directory like State > Agency > date of scrape

There's a 1 second delay between requests to avoid fucking anything up. 

If you don't want to do all of this yourself, you can also grab a scrape dated June 11, 2025 that I formatted into one big spreadsheet [here](https://github.com/JonGerhardson/axon-fusus-analysis-tools/blob/main/flock/flock_all_public_6-11-2025.xlsx). 

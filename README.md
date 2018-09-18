# baytraffic_sharing
The public version of harvesting traffic data using Google directions API and match to the OSM street network, the postprocessing and visualization.

### Setting up
1. Install Python modules
	* Start and connect to a ubuntu EC2 instance `ssh -i private_key.pem ubuntu@ip`. Set the security group to allow only access from known ip address.
    * `sudo apt-get update`
	* Install pip3: `sudo apt-get install python3-pip`
	* Install python modules: `pip3 install numpy pprint`
	* Install and configure Boto 3: follow the `Installation` and `Configuration` sections on [Boto 3 Documentation](http://boto3.readthedocs.io/en/latest/guide/quickstart.html).

2. Get the code:
	* In terminal, run `git clone https://github.com/cb-cities/baytraffic_share.git` to clone the repository.

3. Set Google Key:
	* See [this page](https://developers.google.com/maps/documentation/directions/get-api-key) and follow the `quick guide to getting a key` to get an API key.
	* In the `baytraffic_share` folder that is just cloned, open the [google_key.py](google_key.py) file, replace the `AIza...` part with the API key just obtained. The API key should be enclosed by the quotation mark. Save the change.
	
### Preparing the OSM data
1. Prepare the OSM street data: 
    * Note, this step can also be skipped to use the sample data of San Francisco in [data_repo](data_repo)
    * If decided to harvest the data for another city, in the terminal, change to the `baytraffic` directory, run the following commands to download OSM data. Change the bounding box `bbox` to the one of the target city:     
        `echo "data=[out:json][bbox:37.6040,-123.0137,37.8324,-122.3549];way[highway];(._;>;);out;" > query.osm`   
        `curl -o target.osm -X POST -d @query.osm "http://overpass-api.de/api/interpreter"`
        based on http://overpass-api.de/command_line.html  
    * If harvest data for a big area, use `osm_download_data.py` to separate the OSM results into several smaller files.
        Bay Area `36.8931, -123.5337, 38.8643, -121.2082`  
    * Run [osm_converter.py](osm_converter.py) that converts OSM data downloaded from osm-overpass to convenient format and store the output in [data_repo](data_repo)

### Harvesting the Google data
1. Test run of the main script: [data_harvest.py](data_harvest.py)
    * Once you have the nodes and links json files in [data_repo](data_repo), you can do a test run of the main script. It randomely selects a number of road links, queries the Google directions API for the current travel time for each of these road links ([google_res.py](google_res.py)) and matches it to the corresponding OSM section based on the haversine distance between the end point of the section to the starting point of the link ([haversine.py](haversine.py)).
    * Set the `NUMBER_OF_LINKS` to 5 during the test phase to avoid using up the Google API quota
    * The raw query results and the section-level travel time will be uploaded to the AWS S3 bucket called `baytraffic` or any specified name as in `S3_BUCKET`, with file key `[folder]/[res_or_time]_[query_time].txt`, where `[query_time]` is the date and time that the query is made.
2. Run the main script at fixed time intervals as a crontab job
    * Check if the `data_harvest.py` is executable, e.g., whether there is `x` when doing `ls -l data_harvest.py`. If not, make the script executable with `chmod +x [path-to-data_harvest.py-script]`, e.g., `chmod +x ~/baytraffic/data_harvest.py`
    * Open the crontab editor with `env EDITOR=vim crontab -e`. Enter the insert mode with `i`. Insert `0 */5 * * * /usr/bin/python3 /home/ubuntu/baytraffic_share/data_harvest.py` to run the `data_harvest.py` every 5 hours. Exit the insert mode with `ESC`. Leave the text editor and go back to the terminal using `:x`
    * Use `crontab -l` to view the current job, `mail` to check messages and `crontab -r` to remove the current job.
    * If the crontab is running without error, change `NUMBER_OF_LINKS` in [data_harvest.py](data_harvest.py) at a higher number, e.g., to 500.
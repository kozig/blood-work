## First demo run
- abnormal results gives the following error: An error occurred: 'dict object' has no attribute 'result' 
- It is not sorting the uploaded results by user and stacking the data. Maybe it is because it is only a demo lets query the db.

## Probing the DB
- after checking the DB everything seems to be in order. 

1. double check the error above. Although probably not important since it seems to be an error from the flask demo since the pdf is scraped and added to the db correctly.
2. add additional column in patient_info table to have the first and lastname seperated (maybe skip this for now as this will be trivial to change when neccessary.
3. Start tracking blood-work directory and push to remote repo.

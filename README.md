# Path classifier

This project works as a demonstrator in applying machine learning algorithms to transform data distributed in several
Excel(C) files (specification) into a single target format (here *.xml)

## Publication
The documentation to this project is published under *Novel Unsupervised learning algorithm for data
matching in different files types* on the [priorart-register](https://www.priorartregister.com/publication_detail.php?ott_no=OTT008757)

## Intention
Most companies use Excel(C) to hold and represent data in form of descriptions for devices. Usually this data is not
distributed to a customer in this form rather than in a condensed form in a different file format.  
The intention is to learn a mapping between the specification and the target file in order to generate target files
in case of small changes to the specification (eg. change a value or add a new device).

## Example data
To demonstrate the process the project comes with a test data generator which creates some Excel(C) specification and
xml target file in form of car data for a arbitrary car saloon. The sole purpose for this data is to demonstrate the
functionality as due to machine learning background the algorithm is independent to the underlying data 

### Disclaimer
- Excel(C) is a trademark of Microsoft(C)
- openpyxl is published under the MIT license
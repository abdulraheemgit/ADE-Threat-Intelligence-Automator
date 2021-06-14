# ADE-Threat-Intelligence-Disaminator
This tool will aquire data from APCERT Data Exchange (ADE) and dissaminate the information to the relevent authority

This tool will 
  - automatically log in to the ADE portal and download latest relvent file.
  - then decrypt it wil the PGP key.
  - sort the information for each ip owner (mostlylocal isp)
  - send the sorted files to relevet isp
  - creates a summary report


# ADE-Threat-Intelligence-Disaminator
// A handy tool for the CERT community. //

This tool will aquire data from APCERT Data Exchange (ADE) and dissaminate the information to the relevent authority.


This tool will 
  - automatically log in to the ADE portal and download latest relvent file.
  - then decrypt it with the PGP key.
  - sort the information for each ip owner (mostlylocal isp)
  - send the sorted files to relevet isp
  - creates a summary report

Usage:
python2 ADE.py

If you need any clarification please feel free to contact abdulraheemedu@gmail.com

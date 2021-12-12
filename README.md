# Program for demonstrating Byzantine Agreement with Unknown Participants and Failures

You can find the original paper [here](https://arxiv.org/abs/2102.10442).
The repository consists of the backend and the frontend parts of the program and a report.

## Backend

The backend part is a multithread application with json input. Thus, it can easily be modified to use and run in more computers. The test input files for backend are under the inputs folder.
A simple command for running of the backend from command line:

    python backend\main.py --input-file backend\inputs\input1.json

## Frontend

The backend generates the input file for the frontend. A simple command for running of the frontend from command line:

    python frontend\main.py --input-file output.json

## Report

The report is a small overview of the original paper and the program. It is written in LaTeX.

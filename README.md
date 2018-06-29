# on-the-way

This is a little Python script that helps you sort a list of addresses by *deflection distance*, or how much of a detour they would add to a fixed route (e.g., your commute from home to work), using the Google Maps API.

I wrote it when I was looking for a new family doctor, and sorted a list of every doctor in Kitchener-Waterloo by those most convenient for me.

## Usage

Give it a start and endpoint, and a CSV file with an `address` column using command-line args:

```bash
$ python on_the_way.py "Conestoga Mall, Waterloo, ON" "Davis Centre, University of Waterloo, Waterloo, ON" doctors.csv
```

## Requirements

It should run on Python 2.7 or 3+. It needs the following packages. Exact specifications can be found in [requirements.txt](requirements.txt).

- Google Maps API
- NumPy
- Pandas
- tqdm
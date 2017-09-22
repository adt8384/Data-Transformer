import os
import string # include string methods
import csv # include csv reader, writer format 
import sys # include system package 
import datetime, time # include datetime objects
import json # include json package


# Parses the input csv file to row
# headers and data.
def parse_input_csv_file(csv_file):
  try:
    # open input file in read mode
    with open(csv_file, 'r') as f:
      reader = csv.reader(f)
      # get headers in a list
      row1 = next(reader)
      if not row1:
        sys.exit('No rows found in CSV file.')
        return (None, None, None)
      # key value mapping for row header names and column index 
      _op_index_dict = dict()
      # enumerate generates indexes of list element
      for i, j in enumerate(row1):
        _op_index_dict[j] = i
      # list of data
      _csv_rows = list()
      # read rows through file and append to _csv_rows
      for row in reader:
        _csv_rows.append(row)
      return (_op_index_dict, _csv_rows, row1)
  except IOError as ioe:  
    sys.exit('Cannot open input CSV file.')
  return (None, None, None)

# Parses the given json file to dict.
def parse_transform_json_file(json_file):
  try:
    # open json in read mode
    with open(json_file, 'r') as jfile:
      # json.load converts json file into dict() key value mapping
      data = json.load(jfile)
      if not data:
        sys.exit('Input JSON file is empty')
        return None
      # store key value of transformation and field to operate  
      _op_dict = dict()
      # transforms stores transformations specified in json
      transform_flds = data.get('transforms', None)
      if not transform_flds:
        sys.exit('JSON file seems to have no transform field')
        return None
      # iterate transformations  
      for transform_fld in transform_flds:
        # get operation to perform eg. slugify
        op_type = transform_fld.get('operation', None)
        if not op_type:
          sys.exit('JSON file is missing operation field.')
        # validate operation  
        if not op_type in ('slugify', 'f-to-c', 'hst-to-unix'):
          sys.exit('Operation type in JSON file has invalid value')
        # get field to operate on
        op_val = transform_fld.get('column', None)
        if not op_val:
          sys.exit('JSON file is missing column field.')
        # Populate the dictionary.  
        _op_dict[op_type] = op_val
      return _op_dict
  except IOError as ioe:  
    sys.exit('Failed to open JSON input file.')
  return None
        
        
# Check the transformation value in the CSV file.
def check_trans_val_in_csv(op_index_dict, op_dict):
  # key value mapping of operation from json and 
  # column index to be tranformed from CSV
  _op_trans_index_dict = dict()
  # get recorded date needed for unix (epoch) time for hst-to-unix
  _op_trans_index_dict['RecordedDate'] = op_index_dict.get('RecordedDate', None)
  for op in op_dict:
    op_val = op_dict[op]
    op_index = op_index_dict.get(op_val, None)
    if not op_index:
      sys.exit('Failed to find operation in CSV file.')
    _op_trans_index_dict[op] = op_index  
  return _op_trans_index_dict  

def slugify_transform(_slug_istr):
  # Remove punctuation
  _tstr = _slug_istr.translate(None, string.punctuation)
  # Replace whitespace with hypen
  _tstr = _tstr.replace(" ", "-")
  # Make string to lowercase
  _tstr = _tstr.lower()
  return _tstr

def hst_to_unix_transform(_d, _t):
  try:
    # remove trailing spaces from time
    _htou_str = _d + ' ' + _t
    _htou_str = _htou_str.strip()
    if not _htou_str:
      return str(0)
    # Set HST time zone 
    os.environ['TZ'] = 'HST+10'
    time.tzset()
    # Use the following pattern to get epoch
    pattern = '%m/%d/%y %H:%M:%S'
    # convert to Unix timestamp
    epoch = int(time.mktime(time.strptime(_htou_str, pattern)))
    return str(epoch)
  except ValueError:
    return _t


# Convert Farhenheit to Celsius
def f_to_c_transform(_f_str):
  try:
    _ft = float(_f_str)
    _ct = format( ((float(_ft) - 32) / 1.8), '.2f')
    return str(_ct)
  except ValueError:  
    return _f_str

# Transform the fields.
def transform_csv_fields(_op_trans_index_dict, _csv_rows, hdr, out_file):
  try:
    # create output file in write more
    with open(out_file,'wb') as of:
      # output csv file can be opened in excel
      wr = csv.writer(of, dialect='excel')
      # wite the header fields into output file
      wr.writerow(hdr)
      # get index of RecordedDate from input CSV
      _d_idx = _op_trans_index_dict.get('RecordedDate', None)
      
      # iterate over data rows
      for _csv_row in _csv_rows:
        if not _csv_row:
          continue
        # get index of column for slugify from JSON CSV Column mapping
        _csv_idx = _op_trans_index_dict.get('slugify', None)
        # skip transformation if dont find the index
        # perform slugify transformation.
        if _csv_idx:
          # validation that column index < number of columns 
          # to ensure column exists in input CSV
          if _csv_idx < len(_csv_row):
            slug_str = slugify_transform(_csv_row[_csv_idx])
            # set transformed value
            _csv_row[_csv_idx] =  slug_str

        # get index of column for f-to-c from JSON CSV Column mapping
        _csv_idx = _op_trans_index_dict.get('f-to-c', None)
        # perform f to c transformation.
        if _csv_idx:
          if _csv_idx < len(_csv_row):
            f_to_c_tstr = f_to_c_transform(_csv_row[_csv_idx])
            _csv_row[_csv_idx] = f_to_c_tstr

         # get index of column for hst-to-unix from JSON CSV Column mapping    
        _csv_idx = _op_trans_index_dict.get('hst-to-unix', None)
        # perform hst to unix transformation.
        if _csv_idx:
          if _csv_idx < len(_csv_row):
            if _d_idx is None:
              continue
            _d = _csv_row[_d_idx] # get the date from RecordedDate index
            _t = _csv_row[_csv_idx]
            hst_to_unix_tstr = hst_to_unix_transform(_d, _t) 
            _csv_row[_csv_idx] = hst_to_unix_tstr
        # write row to output CSV
        wr.writerow(_csv_row)
  except IOError as ioe:  
    sys.exit('Output CSV path inaccessible or not found.')
  

    

# check the usage of the program.
# the program needs input csv file, JSON transformation file and output file
if len(sys.argv) < 4:
  print "Usage: python transformers.py <csv_file> <json_file> <output_file>"
  exit()

csv_file = sys.argv[1]      # input csv file
json_file = sys.argv[2]     # JSON transformation file
output_file = sys.argv[3]   # output file


# parse the input csv file to get the header and data
(op_index_dict, csv_rows, row1) = parse_input_csv_file(csv_file)
# parse the JSON input file
op_dict = parse_transform_json_file(json_file)
# get the mapping from transaction json to csv header
op_trans_index_dict = check_trans_val_in_csv(op_index_dict, op_dict)
# transform the CSV fields based on transformation
transform_csv_fields(op_trans_index_dict, csv_rows, row1, output_file)
print "Outfile generated " + output_file 

from optparse import OptionParser

def parse_options():
  # type: () -> (str, str, bool)
  """
  Parses options from arguments

  :return config_filepath: The parsed file path
  """
  parser = OptionParser()
  parser.add_option("-c", "--configfile", dest="filename", help="File for configuration. config.conf by default.",
                    metavar="FILE", default="config.conf")
  parser.add_option("-t", "--testcase", dest="testcase", help="File for test case. Required.",
                    metavar="FILE")
  parser.add_option("-d", "--detail", dest="detail", action="store_true", help="Prints test result in detail", default=False)
  options, args = parser.parse_args()
  config_filepath = options.filename
  test_filepath = options.testcase
  detail_flag = options.detail
  return config_filepath, test_filepath, detail_flag


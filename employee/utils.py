# import codecs

# def safe_decode(data):
#     if isinstance(data, str):
#         return data  # Already decoded
#     try:
#         return data.decode('utf-8')
#     except UnicodeDecodeError:
#         try:
#             return codecs.decode(data, 'latin-1')
#         except UnicodeDecodeError:
#             return codecs.decode(data, 'ISO-8859-1')  # Another fallback

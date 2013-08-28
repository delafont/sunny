def sha1(file_path):
    """
    Return the sha1 hex digest of a file.
    :param file_path: (str) the absolute path to the file.
    """
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(128 * 64), ''):
                sha1.update(chunk)
    except:
        print "Error: impossible to generate a SHA1: %s does not exist anymore." % file_path
    return sha1.hexdigest()

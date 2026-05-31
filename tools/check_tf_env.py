import sys

def main():
    try:
        import tensorflow as tf
        tf_file = getattr(tf, '__file__', None)
        tf_ver = getattr(tf, '__version__', None)
    except Exception as e:
        tf_file = f'ERROR: {e}'
        tf_ver = 'ERROR'

    print('PYTHON_EXECUTABLE:', sys.executable)
    print('TENSORFLOW_FILE:', tf_file)
    print('TENSORFLOW_VERSION:', tf_ver)

if __name__ == '__main__':
    main()

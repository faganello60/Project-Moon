from numpy.distutils.core import setup, Extension

# Define the extension module
ext = Extension(name='gyro', sources=['gyro.f'])

# Setup configuration
setup(
    name='gyro',
    description='Gyrosynchrotron radiation simulation',
    ext_modules=[ext],
)

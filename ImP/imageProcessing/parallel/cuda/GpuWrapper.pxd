from libcpp cimport bool
from cpython.ref cimport PyObject

"""
Definition file for GpuWrapper.pyx.
Mainly definitions of C/C++ code to be used in GpuWrapper.
"""

# References PyObject to OpenCV object conversion code borrowed from OpenCV's own conversion file, cv2.cpp
cdef extern from 'pyopencv_converter.cpp':
    cdef PyObject* pyopencv_from(const Mat& m)
    cdef bool pyopencv_to(PyObject* o, Mat& m)

cdef extern from 'opencv2/imgproc.hpp' namespace 'cv':
    cdef enum InterpolationFlags:
        INTER_NEAREST
        INTER_LINEAR
    cdef enum ColorConversionCodes:
        COLOR_BGR2GRAY

cdef extern from 'opencv2/core/core.hpp':
    cdef int CV_8UC1
    cdef int CV_32FC1

cdef extern from 'opencv2/core/core.hpp' namespace 'cv':
    cdef cppclass Size_[T]:
        Size_() except +
        Size_(T width, T height) except +
        T width
        T height
    ctypedef Size_[int] Size2i
    ctypedef Size2i Size
    cdef cppclass Scalar[T]:
        Scalar() except +
        Scalar(T v0) except +

cdef extern from 'opencv2/core/core.hpp' namespace 'cv':
    cdef cppclass Mat:
        Mat() except +
        void create(int, int, int) except +
        void* data
        int rows
        int cols

cdef extern from 'opencv2/core/cuda.hpp' namespace 'cv::cuda':
    cdef cppclass GpuMat:
        GpuMat() except +
        void upload(Mat arr) except +
        void download(Mat dst) const
    cdef cppclass Stream:
        Stream() except +

cdef extern from 'opencv2/cudawarping.hpp' namespace 'cv::cuda':
    cdef void warpPerspective(GpuMat src, GpuMat dst, Mat M, Size dsize, int flags, int borderMode, Scalar borderValue, Stream& stream)
    # Function using default values
    cdef void warpPerspective(GpuMat src, GpuMat dst, Mat M, Size dsize, int flags)

cdef extern from 'opencv2/imgproc.hpp' namespace 'cv':
    cdef void warpPerspective(Mat src, Mat dst, Mat M, Size dsize, int flags)

cdef extern from 'opencv2/cudaimgproc.hpp' namespace 'cv::cuda':
    cdef void cvtColor(GpuMat src, GpuMat dst, int code) except +

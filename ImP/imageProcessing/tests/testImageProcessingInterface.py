import os
import unittest
from collections import namedtuple
import cv2
from cv2 import aruco
import numpy as np
import os
import pyquaternion
from collections import namedtuple
from ImP.imageProcessing.aerocubeMarker import AeroCubeMarker, AeroCubeFace, AeroCube
from ImP.imageProcessing.imageProcessingInterface import ImageProcessor
from ImP.imageProcessing.settings import ImageProcessingSettings
from ImP.imageProcessing.cameraCalibration import CameraCalibration
from jobs.aeroCubeSignal import ImageEventSignal


class TestImageProcessingInterfaceMethods(unittest.TestCase):
    test_files_path = ImageProcessingSettings.get_test_files_path()
    test_output_path = os.path.join(test_files_path, 'output.png')
    AC_0_FACES_125_PATH = os.path.join(test_files_path, 'capstone_class_photoshoot/AC_0_FACES_125.JPG')
    # create named tuple to help organize test files and expected results of scan
    TestFile = namedtuple('TestFile', 'img_path \
                                       corners \
                                       IDs')
    # struct for image 'marker_4X4_sp6_id0.png'
    TEST_SINGLE_MARKER = TestFile(img_path=os.path.join(test_files_path, 'marker_4X4_sp6_id0.png'),
                                  corners=[np.array([[[82.,  51.],
                                                      [453., 51.],
                                                      [454., 417.],
                                                      [82.,  417.]]])],
                                  IDs=np.array([[0]]))
    # struct for image 'no_markers.jpg'
    TEST_NO_MARKER = TestFile(img_path=os.path.join(test_files_path, 'no_markers.jpg'),
                              corners=[],
                              IDs=None)
    # struct for image '2_ZENITH_0_BACK.jpg'
    TEST_MULT_AEROCUBES = TestFile(img_path=os.path.join(test_files_path, '2_ZENITH_0_BACK.jpg'),
                                   corners=[np.array([[[371.,  446.],
                                                       [396.,  505.],
                                                       [312.,  533.],
                                                       [290.,  471.]]]),
                                            np.array([[[801.,  314.],
                                                       [842.,  359.],
                                                       [779.,  380.],
                                                       [741.,  333.]]])],
                                   IDs=np.array([[12], [4]]))
    # struct for image 'jetson_test1.jpg'
    TEST_JETSON_SINGLE_MARKER = TestFile(img_path=os.path.join(test_files_path, 'jetson_test1.jpg'),
                                         corners=[np.array([[[1., 1.],
                                                             [1., 1.],
                                                             [1., 1.],
                                                             [1., 1.]]])],
                                         IDs=np.array([[0]]))

    def test_init(self):
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        self.assertIsNotNone(imp._img_mat)

    def test_positive_load_image(self):
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        self.assertIsNotNone(ImageProcessor._load_image(self.TEST_SINGLE_MARKER.img_path))

    def test_negative_load_image(self):
        self.assertRaises(OSError, ImageProcessor, self.TEST_SINGLE_MARKER.img_path + "NULL")

    def test_find_fiducial_marker(self):
        # hard code results of operation
        corners, ids = ImageProcessor._simplify_fiducial_arrays(self.TEST_SINGLE_MARKER.corners,
                                                                self.TEST_SINGLE_MARKER.IDs)
        # get results of function
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        test_corners, test_ids = imp._find_fiducial_markers()
        # assert hard-coded results equal results of function
        self.assertTrue(np.array_equal(corners, test_corners))
        self.assertTrue(np.array_equal(ids, test_ids))
        self.assertEqual(type(test_ids).__module__, np.__name__)
        # save output image for visual confirmation
        output_img = imp.draw_fiducial_markers(test_corners, test_ids)
        cv2.imwrite(self.test_output_path, output_img)

    def test_find_fiducial_marker_multiple(self):
        # get results from ImP
        imp = ImageProcessor(self.TEST_MULT_AEROCUBES.img_path)
        corners, ids = imp._simplify_fiducial_arrays(self.TEST_MULT_AEROCUBES.corners, self.TEST_MULT_AEROCUBES.IDs)
        test_corners, test_ids = imp._find_fiducial_markers()
        # assert hard-coded results equal ImP results
        np.testing.assert_allclose(corners, test_corners)
        np.testing.assert_array_equal(ids, test_ids)

    def test_find_fiducial_marker_none(self):
        imp = ImageProcessor(self.TEST_NO_MARKER.img_path)
        corners, ids = imp._simplify_fiducial_arrays(self.TEST_NO_MARKER.corners, self.TEST_NO_MARKER.IDs)
        test_corners, test_ids = imp._find_fiducial_markers()
        np.testing.assert_allclose(corners, test_corners)
        np.testing.assert_array_equal(ids, test_ids)

    def test_simplify_fiducial_arrays(self):
        # No markers
        corners, ids = self.TEST_NO_MARKER.corners, self.TEST_NO_MARKER.IDs
        actual_corners, actual_ids = ImageProcessor._simplify_fiducial_arrays(corners, ids)
        exp_corners, exp_ids = [], []
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertIsInstance(actual_corners, np.ndarray)
        self.assertIsInstance(actual_ids, np.ndarray)
        # One marker
        corners, ids = self.TEST_SINGLE_MARKER.corners, self.TEST_SINGLE_MARKER.IDs
        actual_corners, actual_ids = ImageProcessor._simplify_fiducial_arrays(corners, ids)
        exp_corners, exp_ids = np.array(corners).squeeze(axis=1), np.array(ids).squeeze()
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertEqual(np.shape(actual_corners), (1, 4, 2))
        self.assertEqual(np.shape(actual_ids), (1,))
        self.assertIsInstance(actual_corners, np.ndarray)
        self.assertIsInstance(actual_ids, np.ndarray)
        # Multiple markers
        corners, ids = self.TEST_MULT_AEROCUBES.corners, self.TEST_MULT_AEROCUBES.IDs
        actual_corners, actual_ids = ImageProcessor._simplify_fiducial_arrays(corners, ids)
        exp_corners, exp_ids = np.array(corners).squeeze(axis=1), np.array(ids).squeeze()
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertEqual(np.shape(actual_corners), (2, 4, 2))
        self.assertEqual(np.shape(actual_ids), (2,))
        self.assertIsInstance(actual_corners, np.ndarray)
        self.assertIsInstance(actual_ids, np.ndarray)

    def test_simplify_fiducial_arrays_raises_properly(self):
        markers = self.TEST_MULT_AEROCUBES
        corners, ids = ImageProcessor._simplify_fiducial_arrays(markers.corners, markers.IDs)
        self.assertRaises(AssertionError, ImageProcessor._simplify_fiducial_arrays, corners, ids)

    def test_prepare_fiducial_arrays_for_aruco(self):
        # No markers
        markers = self.TEST_NO_MARKER
        corners, ids = ImageProcessor._simplify_fiducial_arrays(markers.corners, markers.IDs)
        actual_corners, actual_ids = ImageProcessor._prepare_fiducial_arrays_for_aruco(corners, ids)
        exp_corners, exp_ids = [], None
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertNotIsInstance(actual_ids, np.ndarray)
        # One marker
        markers = self.TEST_SINGLE_MARKER
        corners, ids = ImageProcessor._simplify_fiducial_arrays(markers.corners, markers.IDs)
        actual_corners, actual_ids = ImageProcessor._prepare_fiducial_arrays_for_aruco(corners, ids)
        exp_corners, exp_ids = [corners], [ids]
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertEqual(np.shape(actual_corners), (1, 1, 4, 2))
        self.assertEqual(np.shape(actual_ids), (1, 1))
        # Multiple markers
        markers = self.TEST_MULT_AEROCUBES
        corners, ids = ImageProcessor._simplify_fiducial_arrays(markers.corners, markers.IDs)
        actual_corners, actual_ids = ImageProcessor._prepare_fiducial_arrays_for_aruco(corners, ids)
        exp_corners, exp_ids = [[corners[0]], [corners[1]]], [[ids[0]], [ids[1]]]
        np.testing.assert_allclose(actual_corners, exp_corners)
        np.testing.assert_array_equal(actual_ids, exp_ids)
        self.assertEqual(np.shape(actual_corners), (2, 1, 4, 2))
        self.assertEqual(np.shape(actual_ids), (2, 1))

    def test_translate_fiducial_markers_for_aruco_raises_properly(self):
        markers = self.TEST_MULT_AEROCUBES
        self.assertRaises(AssertionError, ImageProcessor._prepare_fiducial_arrays_for_aruco, markers.corners, markers.IDs)

    def test_find_aerocube_marker(self):
        imp = ImageProcessor(self.AC_0_FACES_125_PATH)
        aerocube_markers = imp._find_aerocube_markers()
        [self.assertIsInstance(m, AeroCubeMarker) for m in aerocube_markers]

    def test_find_aerocube_markers_none(self):
        # get hard-coded results
        aerocube_markers = []
        # get ImP results
        imp = ImageProcessor(self.TEST_NO_MARKER.img_path)
        test_markers = imp._find_aerocube_markers()
        self.assertTrue(np.array_equal(aerocube_markers, test_markers))

    def test_identify_aerocubes(self):
        aerocube_ID = 0
        aerocube_face = AeroCubeFace.ZENITH
        corners, _ = ImageProcessor._simplify_fiducial_arrays(self.TEST_SINGLE_MARKER.corners, [[aerocube_ID]])
        marker_list = [AeroCubeMarker(aerocube_ID, aerocube_face, corners[0])]
        aerocube_list = [AeroCube(marker_list)]
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        self.assertEqual(imp._identify_aerocubes(), aerocube_list)

    def test_identify_aerocubes_multiple(self):
        # get hard-coded results
        corners, _ = ImageProcessor._simplify_fiducial_arrays(self.TEST_MULT_AEROCUBES.corners, [[2], [0]])
        aerocube_2_markers = [AeroCubeMarker(2, AeroCubeFace.ZENITH, corners[0])]
        aerocube_0_markers = [AeroCubeMarker(0,   AeroCubeFace.BACK, corners[1])]
        aerocubes = [AeroCube(aerocube_2_markers), AeroCube(aerocube_0_markers)]
        # get ImP results
        imp = ImageProcessor(self.TEST_MULT_AEROCUBES.img_path)
        test_aerocubes = imp._identify_aerocubes()
        # assert equality
        self.assertTrue(np.array_equal(aerocubes, test_aerocubes))

    def test_identify_aerocubes_none(self):
        imp = ImageProcessor(self.TEST_NO_MARKER.img_path)
        self.assertEqual([], imp._identify_aerocubes())

    def test_find_distance(self):
        imp = ImageProcessor(self.TEST_JETSON_SINGLE_MARKER.img_path)
        corners, ids = imp._find_fiducial_markers()
        dist = imp._find_distance(corners)
        print(dist)
        self.assertGreater(dist[0], 0.8)
        self.assertLess(dist[0], 1.0)

    def test_identify_markers_for_storage(self):
        # TODO: needs to be rewritten for new method
        self.fail()
        # get hard-coded results
        corners, _ = ImageProcessor._simplify_fiducial_arrays(self.TEST_SINGLE_MARKER.corners, [[0]])
        marker_list = [AeroCubeMarker(0, AeroCubeFace.ZENITH, corners[0])]
        aerocube_list = [AeroCube(marker_list)]
        # get ImP results
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        scan_results = imp.identify_markers_for_storage()
        # assert equality
        np.testing.assert_array_equal(aerocube_list, scan_results)

    # drawing functions

    def test_draw_fiducial_markers(self):
        imp = ImageProcessor(self.TEST_SINGLE_MARKER.img_path)
        corners, IDs = imp._find_fiducial_markers()
        img = imp.draw_fiducial_markers(corners, IDs)
        self.assertEqual(img.shape, imp._img_mat.shape)

    def test_draw_axis(self):
        imp = ImageProcessor(self.TEST_JETSON_SINGLE_MARKER.img_path)
        rvecs, tvecs = imp._find_pose(imp._find_fiducial_markers()[0])
        img = imp.draw_axis(imp.rodrigues_to_quaternion(rvecs[0]), tvecs[0])
        self.assertIsNotNone(img)

    # pose representation conversions

    def test_rodrigues_to_quaternion_has_identical_rotation(self):
        """
        Confirms the following case:
        http://stackoverflow.com/questions/12933284/rodrigues-into-eulerangles-and-vice-versa
        """
        imp = ImageProcessor(self.TEST_JETSON_SINGLE_MARKER.img_path)
        rvecs, _ = imp._find_pose(imp._find_fiducial_markers()[0])
        test_quat = imp.rodrigues_to_quaternion(rvecs[0])
        # get rotation matrices
        rot_mat_orig = cv2.Rodrigues(rvecs[0])[0]
        rot_mat_quat = test_quat.rotation_matrix
        rot_mat = cv2.multiply(rot_mat_orig, cv2.transpose(rot_mat_quat))
        # test not working for some reason; just test equality of rotation matrices
        # self.assertTrue(np.allclose(rot_mat,
        #                             np.identity(3),
        #                             rtol=1e-02))
        self.assertTrue(np.allclose(rot_mat_orig,
                                    rot_mat_quat,
                                    rtol=1e-02))

    def test_rodrigues_to_quaternion(self):
        imp = ImageProcessor(self.TEST_JETSON_SINGLE_MARKER.img_path)
        rvecs, _ = imp._find_pose(imp._find_fiducial_markers()[0])
        # test value
        test_quat = imp.rodrigues_to_quaternion(rvecs[0])
        # true value
        true_quat = pyquaternion.Quaternion(w=-0.060, x=0.746, y=-0.648, z=-0.140)
        # assert that the str representations are equal (components identical up to 3 decimal places)
        self.assertEqual(str(test_quat), str(true_quat))

    def test_quaternion_to_rodrigues(self):
        rodr = np.array([[ 2.43782719, -2.1174341, -0.45808756]])
        quat = pyquaternion.Quaternion(w=-0.060, x=0.746, y=-0.648, z=-0.140)
        # assert that rotation matrices of Rodrigues representation and Quaternion translated into Rodrigues
        # is close enough (1e-02)
        self.assertTrue(np.allclose(cv2.Rodrigues(rodr)[0],
                                    cv2.Rodrigues(ImageProcessor.quaternion_to_rodrigues(quat))[0],
                                    rtol=1e-02))

if __name__ == '__main__':
    unittest.main()

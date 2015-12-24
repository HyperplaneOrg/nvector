'''
Created on 18. des. 2015

@author: pab
'''
import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal
from nvector import FrameB, FrameE, FrameN, FrameL, Nvector, ECEFvector
from nvector._core import GeoPoint, GeoPath, unit, Pvector  # , diff_nvectors
from nvector.navigator import EARTH_RADIUS_M


class TestFrameE(unittest.TestCase):
    def test_comparisons_with_frame_E(self):
        E = FrameE(name='WGS84')
        E2 = FrameE(a=E.a, f=E.f)
        self.assertEqual(E, E2)
        self.assertEqual(E, E)
        E3 = FrameE(a=E.a, f=0)
        self.assertNotEqual(E, E3)

    def test_compare_with_frame_B(self):
        E = FrameE(name='WGS84')
        E2 = FrameE(name='WGS72')

        n_EB_E = Nvector(unit([[1], [2], [3]]), z=-400, frame=E)
        B = FrameB(n_EB_E, yaw=10, pitch=20, roll=30, degrees=True)
        self.assertEqual(B, B)
        self.assertNotEqual(B, E)

        B2 = FrameB(n_EB_E, yaw=1, pitch=20, roll=30, degrees=True)
        self.assertNotEqual(B, B2)

        B3 = FrameB(n_EB_E, yaw=10, pitch=20, roll=30, degrees=True)
        self.assertEqual(B, B3)

        n_EC_E = Nvector(unit([[1], [2], [2]]), z=-400, frame=E)
        B4 = FrameB(n_EC_E, yaw=10, pitch=20, roll=30, degrees=True)
        self.assertNotEqual(B, B4)

        n_ED_E = Nvector(unit([[1], [2], [3]]), z=-400, frame=E2)
        B5 = FrameB(n_ED_E, yaw=10, pitch=20, roll=30, degrees=True)
        self.assertNotEqual(B, B5)

    def test_A_and_B_to_delta_in_frame_N(self):

        options = dict(frame=FrameE(name='WGS84'), degrees=True)
        pointA = GeoPoint(latitude=1, longitude=2, z=3, **options)
        pointB = GeoPoint(latitude=4, longitude=5, z=6, **options)

        # Find the exact vector between the two positions, given in meters
        # north, east, and down, i.e. find p_AB_N.

        # SOLUTION:
        n_EA_E = pointA.to_nvector()
        p_EA_E = n_EA_E.to_ecef_vector()
        p_EB_E = pointB.to_ecef_vector()
        p_AB_E = p_EB_E - p_EA_E  # (delta decomposed in E).

        frame_N = FrameN(n_EA_E)
        # frame_N = FrameL(n_EA_E, wander_azimuth=0)
        p_AB_N = p_AB_E.change_frame(frame_N)
        p_AB_N = p_AB_N.pvector
        # Step5: Also find the direction (azimuth) to B, relative to north:
        azimuth = np.rad2deg(np.arctan2(p_AB_N[1], p_AB_N[0]))
        # positive angle about down-axis

        print('Ex1, delta north, east, down = {}, {}, {}'.format(p_AB_N[0],
                                                                 p_AB_N[1],
                                                                 p_AB_N[2]))

        print('Ex1, azimuth = {} deg'.format(azimuth))

        self.assertAlmostEqual(p_AB_N[0], 331730.23478089)
        self.assertAlmostEqual(p_AB_N[1], 332997.87498927)
        self.assertAlmostEqual(p_AB_N[2], 17404.27136194)
        self.assertAlmostEqual(azimuth, 45.10926324)

    def test_B_and_delta_in_frame_B_to_C_in_frame_E(self):
        # delta vector from B to C, decomposed in B is given:

        # A custom reference ellipsoid is given (replacing WGS-84):
        frame_E = FrameE(name='WGS72')

        # Position and orientation of B is given 400m above E:
        n_EB_E = Nvector(unit([[1], [2], [3]]), z=-400, frame=frame_E)

        frame_B = FrameB(n_EB_E, yaw=10, pitch=20, roll=30, degrees=True)

        p_BC_B = Pvector(np.r_[3000, 2000, 100].reshape((-1, 1)),
                         frame=frame_B)

        p_BC_E = p_BC_B.to_ecef_vector()

        p_EB_E = n_EB_E.to_ecef_vector()
        p_EC_E = p_EB_E + p_BC_E
        pointC = p_EC_E.to_geo_point()

        lat_EC, long_EC = pointC.latitude_deg, pointC.longitude_deg
        z_EC = pointC.z
        # Here we also assume that the user wants output height (= - depth):
        msg = 'Ex2, Pos C: lat, long = {},{} deg,  height = {} m'
        print(msg.format(lat_EC, long_EC, -z_EC))

        self.assertAlmostEqual(lat_EC, 53.32637826)
        self.assertAlmostEqual(long_EC, 63.46812344)
        self.assertAlmostEqual(z_EC, -406.00719607)

    def test_ECEF_vector_to_geodetic_latitude(self):

        frame_E = FrameE(name='WGS84')
        # Position B is given as p_EB_E ("ECEF-vector")
        position_B = 6371e3 * np.vstack((0.9, -1, 1.1))  # m
        p_EB_E = ECEFvector(position_B, frame_E)

        # Find position B as geodetic latitude, longitude and height
        pointB = p_EB_E.to_geo_point()
        lat, lon, h = pointB.latitude_deg, pointB.longitude_deg, -pointB.z

        msg = 'Ex3, Pos B: lat, lon = {} {} deg, height = {} m'
        print(msg.format(lat, lon, h))
        self.assertAlmostEqual(lat, 39.37874867)
        self.assertAlmostEqual(lon, -48.0127875)
        self.assertAlmostEqual(h, 4702059.83429485)

    def test_geodetic_latitude_to_ECEF_vector(self):

        options = dict(frame=FrameE(name='WGS84'), degrees=True)
        pointB = GeoPoint(latitude=1, longitude=2, z=-3, **options)

        p_EB_E = pointB.to_ecef_vector()
        print('Ex4: p_EB_E = {} m'.format(p_EB_E.pvector.ravel()))

        assert_array_almost_equal(p_EB_E.pvector.ravel(),
                                  [6373290.27721828, 222560.20067474,
                                   110568.82718179])

    def test_great_circle_distance(self):
        options = dict(frame=FrameE(a=6371e3, f=0), degrees=True)
        positionA = GeoPoint(latitude=88, longitude=0, **options)
        positionB = GeoPoint(latitude=89, longitude=-170, **options)
        s_AB, _azia, _azib = positionA.distance_and_azimuth(positionB)

        p_AB_E = positionB.to_ecef_vector() - positionA.to_ecef_vector()
        # The Euclidean distance is given by:
        d_AB = np.linalg.norm(p_AB_E.pvector, axis=0)

        msg = 'Ex5, Great circle distance = {} km, Euclidean distance = {} km'
        print(msg.format(s_AB / 1000, d_AB / 1000))

        self.assertAlmostEqual(s_AB / 1000, 332.45644411)
        self.assertAlmostEqual(d_AB / 1000, 332.41872486)

    def test_alternative_great_circle_distance(self):
        options = dict(frame=FrameE(a=6371e3, f=0), degrees=True)
        positionA = GeoPoint(latitude=88, longitude=0, **options)
        positionB = GeoPoint(latitude=89, longitude=-170, **options)
        path = GeoPath(positionA, positionB)

        s_AB = path.track_distance(method='greatcircle')
        d_AB = path.track_distance(method='euclidean')

        msg = 'Ex5, Great circle distance = {} km, Euclidean distance = {} km'
        print(msg.format(s_AB / 1000, d_AB / 1000))

        self.assertAlmostEqual(s_AB / 1000, 332.45644411)
        self.assertAlmostEqual(d_AB / 1000, 332.41872486)

    def test_exact_ellipsoidal_distance(self):
        options = dict(frame=FrameE(name='WGS84'), degrees=True)
        pointA = GeoPoint(latitude=88, longitude=0, **options)
        pointB = GeoPoint(latitude=89, longitude=-170, **options)
        s_AB, _azia, _azib = pointA.distance_and_azimuth(pointB)

        p_AB_E = pointB.to_ecef_vector() - pointA.to_ecef_vector()
        # The Euclidean distance is given by:
        d_AB = np.linalg.norm(p_AB_E.pvector, axis=0)

        msg = 'Ex5, Great circle distance = {} km, Euclidean distance = {} km'
        print(msg.format(s_AB / 1000, d_AB / 1000))

        self.assertAlmostEqual(s_AB / 1000, 333.94750946834665)
        self.assertAlmostEqual(d_AB / 1000, 333.90962112)

    def test_position_A_and_azimuth_and_distance_to_B(self):
        frame = FrameE(a=EARTH_RADIUS_M, f=0)
        pointA = GeoPoint(latitude=80, longitude=-90, degrees=True, frame=frame)
        pointB, _azimuthb = pointA.geo_point(distance=1000, azimuth=200,
                                             degrees=True)

        lat_B, lon_B = pointB.latitude_deg, pointB.longitude_deg

        print('Ex8, Destination: lat, long = {} {} deg'.format(lat_B, lon_B))
        self.assertAlmostEqual(lat_B, 79.99154867)
        self.assertAlmostEqual(lon_B, -90.01769837)

    def test_intersection(self):

        # Two paths A and B are given by two pairs of positions:
        pointA1 = GeoPoint(10, 20, degrees=True)
        pointA2 = GeoPoint(30, 40, degrees=True)
        pointB1 = GeoPoint(50, 60, degrees=True)
        pointB2 = GeoPoint(70, 80, degrees=True)
        pathA = GeoPath(pointA1, pointA2)
        pathB = GeoPath(pointB1, pointB2)

        pointC = pathA.intersection(pathB)

        lat, lon = pointC.latitude_deg, pointC.longitude_deg
        msg = 'Ex9, Intersection: lat, long = {} {} deg'
        print(msg.format(lat, lon))
        self.assertAlmostEqual(lat, 40.31864307)
        self.assertAlmostEqual(lon, 55.90186788)

    def test_intersection_of_parallell_paths(self):

        # Two paths A and B are given by two pairs of positions:
        pointA1 = GeoPoint(10, 20, degrees=True)
        pointA2 = GeoPoint(30, 40, degrees=True)
        pointB1 = GeoPoint(10, 20, degrees=True)
        pointB2 = GeoPoint(30, 40, degrees=True)
        pathA = GeoPath(pointA1, pointA2)
        pathB = GeoPath(pointB1, pointB2)

        pointC = pathA.intersection(pathB)

        lat, lon = pointC.latitude_deg, pointC.longitude_deg
        msg = 'Ex9, Intersection: lat, long = {} {} deg'
        print(msg.format(lat, lon))
        self.assertTrue(np.isnan(lat))
        self.assertTrue(np.isnan(lon))

    def test_cross_track_distance(self):

        frame = FrameE(a=6371e3, f=0)
        # Position A1 and A2 and B:

        # or input as lat/long in deg:
        pointA1 = GeoPoint(0, 0, degrees=True, frame=frame)
        pointA2 = GeoPoint(10, 0, degrees=True, frame=frame)
        pointB = GeoPoint(1, 0.1, degrees=True, frame=frame)

        pathA = GeoPath(pointA1, pointA2)

        # Find the cross track distance from path A to position B.
        s_xt = pathA.cross_track_distance(pointB, method='greatcircle')
        d_xt = pathA.cross_track_distance(pointB, method='euclidean')

        print(
            'Ex10, Cross track distance = {} m, Euclidean = {} m'.format(
                s_xt,
                d_xt))

        self.assertAlmostEqual(s_xt, 11117.79911015)
        self.assertAlmostEqual(d_xt, 11117.79346741)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
import unittest

from onvifscan import parse as P

CAPS = """<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body>
<tds:GetCapabilitiesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
<tds:Capabilities xmlns:tt="http://www.onvif.org/ver10/schema">
<tt:Device><tt:XAddr>http://192.0.2.10/onvif/device_service</tt:XAddr></tt:Device>
<tt:Media><tt:XAddr>http://192.0.2.10/onvif/Media</tt:XAddr></tt:Media>
<tt:PTZ><tt:XAddr>http://192.0.2.10/onvif/PTZ</tt:XAddr></tt:PTZ>
</tds:Capabilities></tds:GetCapabilitiesResponse></s:Body></s:Envelope>"""

DEVINFO = """<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body>
<tds:GetDeviceInformationResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
<tds:Manufacturer>Acme</tds:Manufacturer><tds:Model>ViewCam</tds:Model>
<tds:FirmwareVersion>1.2.3</tds:FirmwareVersion><tds:SerialNumber>SN1</tds:SerialNumber>
<tds:HardwareId>HW1</tds:HardwareId></tds:GetDeviceInformationResponse></s:Body></s:Envelope>"""

PROFILES = """<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body>
<trt:GetProfilesResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
<trt:Profiles token="Main" fixed="true"><tt:Name>Main</tt:Name>
<tt:VideoSourceConfiguration token="VS1"><tt:Name>VS</tt:Name></tt:VideoSourceConfiguration>
<tt:VideoEncoderConfiguration token="VE1"><tt:Encoding>H265</tt:Encoding>
<tt:Resolution><tt:Width>3840</tt:Width><tt:Height>2160</tt:Height></tt:Resolution>
<tt:RateControl><tt:FrameRateLimit>20</tt:FrameRateLimit><tt:BitrateLimit>8192</tt:BitrateLimit></tt:RateControl>
</tt:VideoEncoderConfiguration>
<tt:PTZConfiguration token="P1"><tt:NodeToken>N</tt:NodeToken></tt:PTZConfiguration>
</trt:Profiles></trt:GetProfilesResponse></s:Body></s:Envelope>"""

TIME = """<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body>
<tds:GetSystemDateAndTimeResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema"><tds:SystemDateAndTime>
<tt:UTCDateTime><tt:Time><tt:Hour>3</tt:Hour><tt:Minute>4</tt:Minute><tt:Second>5</tt:Second></tt:Time>
<tt:Date><tt:Year>2026</tt:Year><tt:Month>1</tt:Month><tt:Day>2</tt:Day></tt:Date></tt:UTCDateTime>
</tds:SystemDateAndTime></tds:GetSystemDateAndTimeResponse></s:Body></s:Envelope>"""


class TestParse(unittest.TestCase):
    def test_scopes_full(self):
        s = P.parse_scopes("onvif://www.onvif.org/Profile/Streaming "
                           "onvif://www.onvif.org/name/My%20Cam "
                           "onvif://www.onvif.org/hardware/HW-1 "
                           "onvif://www.onvif.org/mac/AA:BB:CC:DD:EE:FF "
                           "onvif://www.onvif.org/location/gate")
        self.assertEqual(s["profiles"], ["Streaming"])
        self.assertEqual(s["name"], "My Cam")
        self.assertEqual(s["hardware"], "HW-1")
        self.assertEqual(s["mac"], "aa:bb:cc:dd:ee:ff")
        self.assertEqual(s["location"], "gate")

    def test_scopes_minimal(self):
        s = P.parse_scopes("onvif://www.onvif.org/Profile/Streaming")
        self.assertIsNone(s["mac"])
        self.assertIsNone(s["name"])

    def test_capabilities(self):
        services, malformed = P.parse_capabilities(CAPS)
        self.assertFalse(malformed)
        self.assertEqual(services["media"], "http://192.0.2.10/onvif/Media")
        self.assertIn("ptz", services)

    def test_device_info(self):
        info, _ = P.parse_device_info(DEVINFO)
        self.assertEqual(info["Manufacturer"], "Acme")
        self.assertEqual(info["SerialNumber"], "SN1")

    def test_profiles(self):
        profiles, _ = P.parse_profiles(PROFILES, 1)
        self.assertEqual(len(profiles), 1)
        p = profiles[0]
        self.assertEqual((p["codec"], p["width"], p["height"], p["fps_limit"],
                          p["bitrate_limit_kbps"]), ("H265", 3840, 2160, 20, 8192))
        self.assertTrue(p["ptz_config"])
        self.assertEqual(p["source_token"], "VS1")

    def test_system_datetime(self):
        dt, _ = P.parse_system_datetime(TIME)
        self.assertEqual((dt.year, dt.hour, dt.minute), (2026, 3, 4))

    def test_safe_parse_unbound_prefix(self):
        root, malformed = P.safe_parse("<a><tt:X>1</tt:X></a>")
        self.assertTrue(malformed)
        self.assertIsNotNone(root)

    def test_redact_uri(self):
        self.assertEqual(P.redact_uri("rtsp://admin:secret@192.0.2.1:554/s1"),
                         "rtsp://admin:***@192.0.2.1:554/s1")
        self.assertEqual(P.redact_uri("rtsp://192.0.2.1/s1"), "rtsp://192.0.2.1/s1")


if __name__ == "__main__":
    unittest.main()

"""
@author: Gabriel R. Queiroz, ... 01/11/2024

@description: PyDash Project

An implementation example of a FIXED R2A Algorithm.

the quality list is obtained with the parameter of handle_xml_response() method and the choice
is made inside of handle_segment_size_request(), before sending the message down.

In this algorithm the quality choice is always the same.
"""
import numpy as np
from player.parser import *
from r2a.ir2a import IR2A
import time

class R2AAlgo(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        
        self.segment_throughouts = []
        self.estimated_throughouts = []
        
        self.delta = 0
        self.deviation = 0
        self.k = 21
        self.P0 = 0.2
        
        self.bitrate_constraint = 0 
        self.mu = 0.25

        self.request_time = 0
        self.response_time = 0
        
        self.qi = []
        self.vi = 0
        self.au = 0
        self.av = 0
        self.overall_quality = 0

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        
        self.send_up(msg)        

    def handle_segment_size_request(self, msg):        
        self.request_time = time.perf_counter()
        
        msg.add_quality_id(self.qi[0])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):        
        i = msg.get_segment_id() - 1
        
        self.response_time = time.perf_counter()
        self.segment_throughouts.append(self.response_time - self.request_time)
        
        if i == 0 or i == 1:
            self.estimated_throughouts.append(self.segment_throughouts[i-1])
        else:
            estimated_throughout = (1 - self.delta) * self.estimated_throughouts[i-2] + self.delta * self.segment_throughouts[i-1]
            self.estimated_throughouts.append(estimated_throughout)
        
        self.deviation = np.abs(self.segment_throughouts[i] - self.estimated_throughouts[i]) / self.estimated_throughouts[i] 
        self.delta = 1 / (1 + np.exp(-self.k * (self.deviation - self.P0)))
        
        self.bitrate_constraint = (1 - self.mu) * self.estimated_throughouts[i]
        
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

# print("mpd info            >>>>>>", self.parsed_mpd.get_mpd_info())
# print("period info         >>>>>>", self.parsed_mpd.get_period_info())
# print("program info        >>>>>>", self.parsed_mpd.get_program_info())
# print("adaptation set info >>>>>>", self.parsed_mpd.get_adaptation_set_info())
# print("title               >>>>>>", self.parsed_mpd.get_title())
# print("segment template    >>>>>>", self.parsed_mpd.get_segment_template())
# print("first level adp set  >>>>>>", self.parsed_mpd.get_first_level_adp_set())

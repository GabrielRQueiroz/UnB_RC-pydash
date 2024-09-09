"""
@author: Gabriel R. Queiroz (221020870),
         Giovanna A. Franceschi (211043496), 
         Wesley R. S. Lira (170072291)
         08/09/2024

@description: PyDash Project

This is an R2A algorithm that selects the best quality level for each segment based on the estimated throughput and the measured throughput of the previous segment.
It  uses a sigmoid function to calculate the deviation between the estimated and measured throughputs 
and then uses a bitrate constraint to select the best quality level that is less than the constraint.
Finally, it uses a variable mu in pair with the estimated throughput to update the bitrate constraint.

"""
import numpy as np
from player.parser import *
from r2a.ir2a import IR2A
import time

class R2AAlgo(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        
        self.segment_throughputs = []
        self.estimated_throughputs = []
        
        self.delta = 0
        self.deviation = 0
        self.k = 21
        self.P0 = 0.2
        
        self.bitrate_constraint = 0 
        self.mu = 0.25

        self.request_time = 0
        self.response_time = 0
        
        self.qi = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        
        self.response_time = time.perf_counter()

        # OBTENÇÃO DA VAZÃO
        measured_throughput = msg.get_bit_length() / (self.response_time - self.request_time)
        self.segment_throughputs.append(measured_throughput)
        
        self.estimated_throughputs.append(self.qi[0])
        
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        
        selected = self.qi[0]
        arr = np.asarray(self.qi)
        
        # OBTEM MELHOR ALTERNATIVA MENOR QUE O LIMITE DE BITRATE
        arr = arr[np.abs(arr) < self.bitrate_constraint]
        
        if np.size(arr) > 0:
            selected = arr[-1]

        msg.add_quality_id(selected) 
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        # ÍNDICE DO SEGMENTO ATUAL
        i = msg.get_segment_id()
        
        self.response_time = time.perf_counter()
        
        # OBTENÇÃO DA VAZÃO DO SEGMENTO ATUAL
        measured_throughput = msg.get_bit_length() / (self.response_time - self.request_time)
        self.segment_throughputs.append(measured_throughput) 
             
        # CÁLCULOS DE p E ∂
        self.deviation = np.abs(self.segment_throughputs[i] - self.estimated_throughputs[i-1]) / self.estimated_throughputs[i-1] 
        self.delta = 1 / (1 + np.exp(-self.k * (self.deviation - self.P0)))
        
        # OBTENÇÃO DA VAZÃO ESTIMADO
        if i == 1 or i == 2:
            self.estimated_throughputs.append(self.segment_throughputs[i])
        else:
            estimated_throughout = (1 - self.delta) * self.estimated_throughputs[i-1] + self.delta * self.segment_throughputs[i]
            self.estimated_throughputs.append(estimated_throughout)
        
        self.bitrate_constraint = (1 - self.mu) * self.estimated_throughputs[i]
        
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
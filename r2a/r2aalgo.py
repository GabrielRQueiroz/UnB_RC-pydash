"""
@author: Gabriel R. Queiroz, ... 01/11/2024

@description: PyDash Project

An implementation example of a FIXED R2A Algorithm.

the quality list is obtained with the parameter of handle_xml_response() method and the choice
is made inside of handle_segment_size_request(), before sending the message down.

In this algorithm the quality choice is always the same.
"""
import numpy as np
import scipy
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
        self.mu = 0.1

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
        
        # OBTENÇÃO DA VAZÃO ESTIMADO
        if i == 1 or i == 2:
            self.estimated_throughputs.append(self.segment_throughputs[i-1])
        else:
            estimated_throughout = (1 - self.delta) * self.estimated_throughputs[i-2] + self.delta * self.segment_throughputs[i-1]
            self.estimated_throughputs.append(estimated_throughout)
        
        # CÁLCULOS DE p E ∂
        self.deviation = np.abs(self.segment_throughputs[i] - self.estimated_throughputs[i]) / self.estimated_throughputs[i] 
        self.delta = 1 / (1 + np.exp(-self.k * (self.deviation - self.P0)))
        
        self.bitrate_constraint = (1 - self.mu) * self.estimated_throughputs[i]
        
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
        # playback_qi = np.array(self.whiteboard.get_playback_qi())
        # playback_pauses = np.array(self.whiteboard.get_playback_pauses())
        # playback_buffer_size = np.array(self.whiteboard.get_playback_buffer_size())
        
        # statistics = [
        #     f'Playback history >>>>>>>>>>>>\n{self.whiteboard.get_playback_history()}\n\n',
        #     f'Playback segment size time >>>>>>>>>>>>\n{self.whiteboard.get_playback_segment_size_time_at_buffer()}\n\n',
        #     f'Buffer >>>>>>>>>>>>\n{self.whiteboard.get_buffer()}\n\n',
        #     f'Playback QI >>>>>>>>>>>>\n{self.whiteboard.get_playback_qi()}\n\n',
        #     f'Playback pauses >>>>>>>>>>>>\n{self.whiteboard.get_playback_pauses()}\n\n',
        #     f'Playback buffer size >>>>>>>>>>>>\n{self.whiteboard.get_playback_buffer_size()}\n\n'
        # ]
        # with open(f'{time.ctime(time.time())}', 'w') as f:
        #     f.writelines(statistics)
                

# print("mpd info            >>>>>>", self.parsed_mpd.get_mpd_info())
# print("period info         >>>>>>", self.parsed_mpd.get_period_info())
# print("program info        >>>>>>", self.parsed_mpd.get_program_info())
# print("adaptation set info >>>>>>", self.parsed_mpd.get_adaptation_set_info())
# print("title               >>>>>>", self.parsed_mpd.get_title())
# print("segment template    >>>>>>", self.parsed_mpd.get_segment_template())
# print("first level adp set  >>>>>>", self.parsed_mpd.get_first_level_adp_set())
from tl_controller.static.constants import FLOWS_VALUES, TRAFFIC_TYPE_TL_ALGORITHMS


class Analyzer:

    def __init__(self):
        # High values
        self.high_vehs_per_hour = FLOWS_VALUES['high']['vehsPerHour']
        self.high_vehs_range = FLOWS_VALUES['high']['vehs_range']
        # Medium values
        self.med_vehs_per_hour = FLOWS_VALUES['med']['vehsPerHour']
        self.med_vehs_range = FLOWS_VALUES['med']['vehs_range']
        # Low values
        self.low_vehs_per_hour = FLOWS_VALUES['low']['vehsPerHour']
        self.low_vehs_range = FLOWS_VALUES['low']['vehs_range']
        # Very Low values
        self.very_low_vehs_per_hour = FLOWS_VALUES['very_low']['vehsPerHour']
        self.very_low_vehs_range = FLOWS_VALUES['very_low']['vehs_range']

        # Get bounds, divided by 3 as it is the values it fits better the 5 minute window
        self.very_low_lower_bound = 0
        self.very_low_upper_bound = round((self.very_low_vehs_per_hour + self.very_low_vehs_range) / 3)
        self.low_upper_bound = round((self.low_vehs_per_hour + self.low_vehs_range) / 3)
        self.med_upper_bound = round((self.med_vehs_per_hour + self.med_vehs_range) / 3)
        self.high_upper_bound = round((self.high_vehs_per_hour + self.high_vehs_range) / 3)

    def analyze_current_traffic_flow(self, passing_veh_n_s, passing_veh_e_w):
        traffic_type = -1

        if self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound and self.very_low_lower_bound <= \
                passing_veh_e_w <= self.very_low_upper_bound:
            traffic_type = 0
        elif self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound <= passing_veh_e_w \
                <= self.low_upper_bound:
            traffic_type = 1
        elif self.low_upper_bound >= passing_veh_n_s >= self.very_low_upper_bound >= passing_veh_e_w \
                >= self.very_low_lower_bound:
            traffic_type = 2
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound and self.very_low_upper_bound <= \
                passing_veh_e_w <= self.low_upper_bound:
            traffic_type = 3
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound <= passing_veh_e_w <= \
                self.med_upper_bound:
            traffic_type = 4
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            traffic_type = 5
        elif self.med_upper_bound >= passing_veh_n_s >= self.low_upper_bound >= passing_veh_e_w >= \
                self.very_low_upper_bound:
            traffic_type = 6
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound and self.low_upper_bound <= \
                passing_veh_e_w <= self.med_upper_bound:
            traffic_type = 7
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound <= passing_veh_e_w <= \
                self.high_upper_bound:
            traffic_type = 8
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.very_low_upper_bound <= \
                passing_veh_e_w <= self.low_upper_bound:
            traffic_type = 9
        elif self.high_upper_bound >= passing_veh_n_s >= self.med_upper_bound >= passing_veh_e_w >= \
                self.low_upper_bound:
            traffic_type = 10
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            traffic_type = 11

        return traffic_type

    def analyzer_tl_algorithm(self, traffic_type):
        return TRAFFIC_TYPE_TL_ALGORITHMS[str(traffic_type)]

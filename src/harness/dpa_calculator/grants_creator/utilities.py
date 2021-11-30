from dpa_calculator.grants_creator.cbsds_creator import CbsdsCreator, UE_PER_AP_BY_REGION_TYPE
from dpa_calculator.grants_creator.cbsds_creator_access_point import CbsdsCreatorAccessPoint
from dpa_calculator.grants_creator.cbsds_creator_user_equipment import CbsdsCreatorUserEquipment
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utilities import get_region_type


def get_cbsds_creator(dpa_zone: AreaCircle, is_user_equipment: bool, number_of_aps: int) -> CbsdsCreator:
    region_type = get_region_type(coordinates=dpa_zone.center_coordinates)
    ue_per_ap = UE_PER_AP_BY_REGION_TYPE[region_type]
    number_of_cbsds = number_of_aps * ue_per_ap if is_user_equipment else number_of_aps
    cbsds_creator_class = CbsdsCreatorUserEquipment if is_user_equipment else CbsdsCreatorAccessPoint
    return cbsds_creator_class(dpa_zone=dpa_zone, number_of_cbsds=number_of_cbsds)

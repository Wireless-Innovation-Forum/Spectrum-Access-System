from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsCreator
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator_access_point import CbsdsCreatorAccessPoint
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator_user_equipment import CbsdsCreatorUserEquipment
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NUMBER_OF_UES_PER_AP_BY_REGION_TYPE
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.utilities import get_region_type


def get_cbsds_creator(cbsd_category: CbsdCategories, dpa_zone: AreaCircle, is_user_equipment: bool, number_of_aps: int) -> CbsdsCreator:
    region_type = get_region_type(coordinates=dpa_zone.center_coordinates)
    ue_per_ap = NUMBER_OF_UES_PER_AP_BY_REGION_TYPE[cbsd_category][region_type]
    number_of_cbsds = number_of_aps * ue_per_ap if is_user_equipment else number_of_aps
    cbsds_creator_class = CbsdsCreatorUserEquipment if is_user_equipment else CbsdsCreatorAccessPoint
    return cbsds_creator_class(cbsd_category=cbsd_category, dpa_zone=dpa_zone, number_of_cbsds=number_of_cbsds)

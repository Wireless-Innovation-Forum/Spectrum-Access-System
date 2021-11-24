from dpa_calculator.grants_creator.grants_creator import GrantsCreator, UE_PER_AP_BY_REGION_TYPE
from dpa_calculator.grants_creator.grants_creator_ap import GrantsCreatorAp
from dpa_calculator.grants_creator.grants_creator_ue import GrantsCreatorUe
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import get_region_type


def get_grants_creator(dpa_zone: AreaCircle, is_user_equipment: bool, number_of_aps: int) -> GrantsCreator:
    region_type = get_region_type(coordinates=dpa_zone.center_coordinates)
    ue_per_ap = UE_PER_AP_BY_REGION_TYPE[region_type]
    number_of_cbsds = number_of_aps * ue_per_ap if is_user_equipment else number_of_aps
    grants_creator_class = GrantsCreatorUe if is_user_equipment else GrantsCreatorAp
    return grants_creator_class(dpa_zone=dpa_zone, number_of_cbsds=number_of_cbsds)

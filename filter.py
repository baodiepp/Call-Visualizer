"""
CSC148, Winter 2023
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import time
import datetime
from call import Call
from customer import Customer

# Map upper-left and bottom-right coordinates (long, lat).
MAP_MIN = (-79.697878, 43.799568)
MAP_MAX = (-79.196382, 43.576959)


# from application import find_customer_by_id


class Filter:
    """ A class for filtering customer data on some criterion. A filter is
    applied to a set of calls.

    This is an abstract class. Only subclasses should be instantiated.
    """

    def __init__(self) -> None:
        pass

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Return a list of all calls from <data>, which match the filter
        specified in <filter_string>.

        The <filter_string> is provided by the user through the visual prompt,
        after selecting this filter.
        The <customers> is a list of all customers from the input dataset.

         If the filter has
        no effect or the <filter_string> is invalid then return the same calls
        from the <data> input.

        Note that the order of the output matters, and the output of a filter
        should have calls ordered in the same manner as they were given, except
        for calls which have been removed.

        Precondition:
        - <customers> contains the list of all customers from the input dataset
        - all calls included in <data> are valid calls from the input dataset
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        raise NotImplementedError


class ResetFilter(Filter):
    """
    A class for resetting all previously applied filters, if any.
    """

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Reset all the applied filters. Return a List containing all the
        calls corresponding to <customers>.
        The <data> and <filter_string> arguments for this type of filter are
        ignored.

        Precondition:
        - <customers> contains the list of all customers from the input dataset
        """
        filtered_calls = []
        for c in customers:
            customer_history = c.get_history()
            # only take outgoing calls, we don't want to include calls twice
            filtered_calls.extend(customer_history[0])
        return filtered_calls

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Reset all of the filters applied so far, if any"


class CustomerFilter(Filter):
    """
    A class for selecting only the calls from a given customer.
    """

    def apply(self, customers: list[Customer], data: list[Call],
              filter_string: str) -> list[Call]:
        """ Return a list of all unique calls from <data> made or
        received by the customer with the id specified in <filter_string>.

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains a valid
        customer ID.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        # valid number id
        if not filter_string.isnumeric():
            return data

        # find correct customer
        customer = None
        for cust in customers:
            if cust.get_id() == float(filter_string):
                customer = cust

        if not customer:
            return data

        calls = list(set(call for call in
                         customer.get_history()[0] + customer.get_history()[1]
                         if call in data))
        return calls

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Filter events based on customer ID"


class DurationFilter(Filter):
    """
    A class for selecting only the calls lasting either over or under a
    specified duration.
    """

    def apply(self, customers: list[Customer], data: list[Call],
              filter_string: str) -> list[Call]:
        """ Return a list of all unique calls from <data> with a duration
        of under or over the time indicated in the <filter_string>.

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains the following
        input format: either "Lxxx" or "Gxxx", indicating to filter calls less
        than xxx or greater than xxx seconds, respectively.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        # Check if the filter string is valid
        if not filter_string.startswith(('L', 'l', 'G', 'g')):
            return data

        # Extract the filter parameters
        comparison_operator = filter_string[0].lower()
        duration = filter_string[1:]

        # Check if duration is a valid number
        if not duration.isnumeric() or not 0 <= float(duration) <= 999:
            return data

        duration = float(duration)

        # Filter calls based on duration and comparison operator
        calls = []
        for call in data:
            if comparison_operator == "l" and call.duration < duration and \
                    call not in calls:
                calls.append(call)
            elif comparison_operator == "g" and call.duration > duration and \
                    call not in calls:
                calls.append(call)

        return calls

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Filter calls based on duration; " \
               "L### returns calls less than specified length, G### for greater"


class LocationFilter(Filter):
    """
    A class for selecting only the calls that took place within a specific area
    """

    def apply(self, customers: list[Customer], data: list[Call],
              filter_string: str) -> list[Call]:
        """ Return a list of all unique calls from <data>, which took
        place within a location specified by the <filter_string>
        (at least the source or the destination of the event was
        in the range of coordinates from the <filter_string>).

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains four valid
        coordinates within the map boundaries.
        These coordinates represent the location of the lower left corner
        and the upper right corner of the search location rectangle,
        as 2 pairs of longitude/latitude coordinates, each separated by
        a comma and a space:
          lowerLong, lowerLat, upperLong, upperLat
        Calls that fall exactly on the boundary of this rectangle are
        considered a match as well.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        positions = filter_string.split(', ')
        if len(positions) == 4 and positions[0].isnumeric() and \
                positions[1].isnumeric() and positions[2].isnumeric() and \
                positions[3].isnumeric():
            lower_left = (float(positions[0]), float(positions[1]))
            upper_right = (float(positions[2]), float(positions[3]))
        else:
            return data

        calls = []
        for call in data:
            if (valid_location(call.dst_loc, lower_left, upper_right)) or \
                    (valid_location(call.src_loc, lower_left, upper_right)) \
                    and (call not in calls):
                calls.append(call)
        return calls

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI
        menu the main
        """
        return "Filter calls made or received in a given rectangular area. " \
               "Format: \"lowerLong, lowerLat, " \
               "upperLong, upperLat\" (e.g., -79.6, 43.6, -79.3, 43.7)"


def valid_location(coord: tuple[float, float], lower_left: tuple[float, float],
                   upper_right: tuple[float, float]) -> bool:
    """
    check if the coordinate <coord> is in the intended target. return bool
    """

    coord_x = coord[0]
    coord_y = coord[1]
    lower_left_x = lower_left[0]
    lower_left_y = lower_left[1]
    upper_right_x = upper_right[0]
    upper_right_y = upper_right[1]
    map_lower_left_x = -79.697878
    map_lower_left_y = 43.576959
    map_upper_right_x = -79.196382
    map_upper_right_y = 43.799568

    in_frame = (upper_right_x >= coord_x >= lower_left_x) and \
               (upper_right_y >= coord_y >= lower_left_y)

    in_map = (map_upper_right_x >= coord_x >= map_lower_left_x) and \
             (map_upper_right_y >= coord_y >= map_lower_left_y)

    return in_map and in_frame


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'time', 'datetime', 'call', 'customer'
        ],
        'max-nested-blocks': 4,
        'allowed-io': ['apply', '__str__'],
        'disable': ['W0611', 'W0703'],
        'generated-members': 'pygame.*'
    })

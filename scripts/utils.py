import logging
import math
import random
from operator import attrgetter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.rcsetup as rcsetup
import numpy as np

logger = logging.getLogger("Toolbox")

#
# mTSP specific initializer
#


def find_max_index(route, vehicle_idx, instance):
    max_demand = instance["vehicles"][vehicle_idx]["capacity"]
    r_route_demand = 0
    for r_idx, store in enumerate(route[::-1]):
        r_route_demand += instance["stores"][store]["demand"]
        if r_route_demand > max_demand:
            return len(route) - r_idx
    return 0


def find_min_index(route, vehicle_idx, instance):
    max_demand = instance["vehicles"][vehicle_idx]["capacity"]
    route_demand = 0
    for idx, store in enumerate(route):
        route_demand += instance["stores"][store]["demand"]
        if route_demand > max_demand:
            return idx
    return len(route)


def correct_route(store_count, instance, ind):
    routes, route_idxs = ind[:store_count], ind[store_count:]

    valid_route_idxs = []
    route_start_idx = 0
    for vehicle_idx, route_finish_idx in enumerate(route_idxs + [store_count]):
        min_index = find_min_index(
            routes[route_start_idx:route_finish_idx], vehicle_idx, instance
        )
        valid_route_idxs.append(route_start_idx + min_index)
        route_start_idx = route_start_idx + min_index
    # Remove last one
    valid_route_idxs = valid_route_idxs[:-1]

    reversed_valid_route_idxs = []
    route_finish_idx = store_count
    for r_vehicle_idx, route_start_idx in enumerate(valid_route_idxs[::-1] + [0]):
        vehicle_idx = len(valid_route_idxs) - r_vehicle_idx
        max_index = find_max_index(
            routes[route_start_idx:route_finish_idx],
            vehicle_idx,
            instance,
        )
        reversed_valid_route_idxs.append(route_start_idx + max_index)
        route_finish_idx = route_start_idx + max_index
    # Remove last one
    reversed_valid_route_idxs = reversed_valid_route_idxs[:-1]

    return routes + reversed_valid_route_idxs[::-1]


def valid_route_capacity(route, vehicle_idx, instance):
    """
    Given a route and a vehicle we check that the vehicle can fulfill the route's demand.
    """
    max_demand = instance["vehicles"][vehicle_idx]["capacity"]
    route_demand = 0
    for store in route:
        route_demand += instance["stores"][store]["demand"]
        if route_demand > max_demand:
            return False
    return True


def validate_capacities(individual, store_count, instance):
    # TODO: si vemos que falla en alguna implementamos esto:
    # Queremos recorrer al individuo e ir llevando la carga total de cada vehículo.
    # Si vemos que alcanza, está todo bien y seguimos, sino, cortamos ahí y le pasamos las tiendas restantes al siguiente camión.
    # Si el último camión tiene tiendas sobrantes, entonces movemos la parte 1 para darle esas al primer camión y volvermos a arrancar.

    routes, route_idxs = individual[:store_count], individual[store_count:]
    route_start_idx = 0
    for vehicle_idx, route_finish_idx in enumerate(route_idxs + [store_count]):
        if not valid_route_capacity(
            routes[route_start_idx:route_finish_idx], vehicle_idx, instance
        ):
            return (
                False,
                vehicle_idx,
                routes[route_start_idx:route_finish_idx],
                route_start_idx,
                route_finish_idx,
            )
        route_start_idx = route_finish_idx
    return True, None, None, None, None


def part2_initializer(ind, instance, type="greedy"):
    vehicle_count = len(instance["vehicles"])
    if type == "uniform":
        step = math.ceil(len(ind) / vehicle_count)
        return [idx * step + step for idx in range(vehicle_count - 1)]
    if type == "choice":
        return sorted(
            random.choices(range(len(instance["stores"]) - 1), k=vehicle_count - 1)
        )
    if type == "random_greedy":
        route_idx = [0] * (vehicle_count - 1)
        start_idx = random.choice(range(vehicle_count - 1))
        # TODO: finish
        return []
    if type == "greedy":
        route_idx = []
        current_store_idx = 0
        for vehicle in range(vehicle_count - 1):
            current_store_idx -= 1
            capacity = instance["vehicles"][vehicle]["capacity"]
            demand = 0
            while (
                current_store_idx < len(instance["stores"]) - 1 and capacity >= demand
            ):
                current_store_idx += 1
                if current_store_idx < len(instance["stores"]) - 1:
                    demand += instance["stores"][ind[current_store_idx]]["demand"]
            route_idx.append(current_store_idx)

        # Fill the remaining vehicles with the last index
        for vehicle in range(len(route_idx), vehicle_count - 1):
            route_idx.append(route_idx[-1])

        return route_idx


def init_iterate_and_distribute(
    container, instance=None, part2_type="choice", assert_validation=False
):
    if not instance:
        raise ValueError("`instance` cannot be None.")

    store_count = len(instance["stores"]) - 1

    # routes
    individual = random.sample(range(store_count), store_count)
    # route assignment
    route_idx = part2_initializer(individual, instance, type=part2_type)
    individual.extend(route_idx)

    individual = correct_route(store_count, instance, individual)
    if assert_validation:
        valid, vehicle_idx, route, s_idx, f_idx = validate_capacities(
            individual, store_count, instance
        )
        if route:
            demands = [
                store["demand"]
                for idx, store in enumerate(instance["stores"])
                if idx in route
            ]
        assert valid, (
            "A vehicle has more demand than capacity.\n"
            + str(instance["vehicles"][vehicle_idx])
            + f" {s_idx} {f_idx}"
            + "\n"
            + ", ".join(str(demand) for demand in demands)
            + "\n"
            + str(sum(demands))
        )

    return container(individual)


#
# Wrappers to make operators work only on one part of the genome.
#


def part_one_edit(func, part_one_len):
    def apply_part_one(*args):
        part1 = slice(part_one_len)
        parts = [ind[part1] for ind in args]
        for updated, original in zip(func(*parts), args):
            original[part1] = updated
        return args

    return apply_part_one


def part_two_edit(func, part_one_len):
    def apply_part_two(*args):
        part2 = slice(part_one_len, None)
        parts = [ind[part2] for ind in args]
        for updated, original in zip(func(*parts), args):
            original[part2] = updated
        return args

    return apply_part_two


#
# Mutation operators
#


def swap_op(ind):
    # Swap two genes of the individual.
    idx1 = random.randint(0, len(ind) - 1)
    idx2 = random.randint(0, len(ind) - 1)
    ind[idx1], ind[idx2] = ind[idx2], ind[idx1]
    return (ind,)


def inc_op(max_value, ind):
    # Sums one to a gene and substracts one to other.
    inc_idx = random.randint(0, len(ind) - 1)

    if ind[inc_idx] + 1 <= max_value and (
        inc_idx == len(ind) - 1 or ind[inc_idx] < ind[inc_idx + 1]
    ):
        ind[inc_idx] += 1
    return (ind,)


def dec_op(ind):
    # Sums one to a gene and substracts one to other.
    dec_idx = random.randint(0, len(ind) - 1)
    if ind[dec_idx] - 1 >= 0 and (dec_idx == 0 or ind[dec_idx - 1] <= ind[dec_idx]):
        ind[dec_idx] -= 1
    return (ind,)


def regenerate_op(ind, max_value):
    ind_len = len(ind)
    ind = random.sample(range(max_value), ind_len)
    ind.sort()
    return (ind,)


def reverse_op(ind):
    idx1 = random.randint(0, len(ind) - 3)
    idx2 = random.randint(idx1 + 2, len(ind) - 1)
    ind[idx1:idx2] = reversed(ind[idx1:idx2])
    return (ind,)


#
# Evaluation function
#


def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def eval_route(route, v_idx, instance):
    t = cost = 0

    prev_store = instance["stores"][-1]
    for store_idx in route:
        store = instance["stores"][store_idx]
        t += calculate_distance(*prev_store["position"], *store["position"])

        ready_time, due_date = store["window"]
        if t < ready_time:
            t = ready_time
        t += store["service_time"]
        cost += max(0, t - due_date)

        prev_store = store

    # Add return to deposit time
    t += calculate_distance(
        *prev_store["position"], *instance["stores"][-1]["position"]
    )
    return cost + t * instance["vehicles"][v_idx]["rate"]


def eval_routes(individual, instance=None):
    if not instance:
        raise ValueError("`instance` cannot be None.")

    store_count = len(instance["stores"]) - 1
    routes, route_idxs = individual[:store_count], individual[store_count:]

    cost = 0
    route_start_idx = 0
    for v_idx, route_finish_idx in enumerate(route_idxs + [store_count]):
        cost += eval_route(routes[route_start_idx:route_finish_idx], v_idx, instance)
        route_start_idx = route_finish_idx

    return (cost,)


#
# Drawing tools
#


def draw_individual(ind, stores, gen, run_name, save_fig=False):
    """
    ind: Chromosome
    stores: np.array shape: (#stores,2) with the x and y coordinates of each store.
    """
    num_stores = len(stores) - 1
    fig, ax = plt.subplots(
        1, 2, sharex=True, sharey=True, figsize=(15, 7.5)
    )  # Prepare 2 plots
    ax[0].set_title("Raw nodes")
    ax[1].set_title("Optimized tours")
    gist_rainbow = plt.cm.gist_rainbow
    idx = np.linspace(0, 1, len(ind[num_stores:]))
    ax[0].set_prop_cycle(rcsetup.cycler("color", gist_rainbow(idx)))
    ax[1].set_prop_cycle(rcsetup.cycler("color", gist_rainbow(idx)))
    ax[0].set_box_aspect(1)
    ax[1].set_box_aspect(1)

    start = 0
    for i, finish in enumerate(np.append(ind[num_stores:], num_stores)):
        ind_slice = ind[start:finish]
        store_slice = stores[ind_slice]
        res = ax[0].scatter(
            store_slice[:, 0], store_slice[:, 1], marker=f"${i}$"
        )  # plot A
        ax[1].scatter(store_slice[:, 0], store_slice[:, 1])  # plot B
        for j in range(len(ind_slice) - 1):
            start_node = ind_slice[j]
            start_pos = stores[start_node]
            next_node = ind_slice[j + 1]
            end_pos = stores[next_node]
            ax[1].annotate(
                "",
                xy=start_pos,
                xycoords="data",
                xytext=end_pos,
                textcoords="data",
                arrowprops=dict(
                    arrowstyle="->",
                    connectionstyle="arc3",
                    color=res.get_facecolors()[0],
                ),
            )
        start = finish
    plt.title(f"Job: {run_name} - Gen: {gen} - Fitness: {ind.fitness.values[0]:.2f}")
    if run_name is not None and save_fig:
        output_path = Path("results") / run_name / "analysis" / f"gen{gen}.jpg"
        plt.savefig(output_path)
    else:
        plt.show()
    plt.close()


def selInverseRoulette(individuals, k, fit_attr="fitness"):
    """Select *k* individuals from the input *individuals* using *k*
    spins of a roulette. The selection is made by looking only at the first
    objective of each individual. The list returned contains references to
    the input *individuals*.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list of selected individuals.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.

    .. warning::
       The roulette selection by definition cannot be used for minimization
       or when the fitness can be smaller or equal to 0.
    """

    s_inds = sorted(individuals, key=attrgetter(fit_attr), reverse=True)
    sum_fits = sum(10000 / getattr(ind, fit_attr).values[0] for ind in individuals)
    chosen = []
    for i in range(k):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += 10000 / getattr(ind, fit_attr).values[0]
            if sum_ > u:
                chosen.append(ind)
                break

    return chosen

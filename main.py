import random

from deap import base, creator, tools

from utils import (
    eval_routes,
    inc_dec,
    init_iterate_and_distribute,
    part_one_edit,
    part_two_edit,
    swap_op,
)

random.seed(0)

current_instance = {
    "stores": [
        {
            "position": (35.00, 35.00),
            "demand": 0.00,
            "window": (0.00, 230.00),
            "service_time": 0.00,
        },
        {
            "position": (41.00, 49.00),
            "demand": 10.00,
            "window": (161.00, 171.00),
            "service_time": 10.00,
        },
    ],
    "vehicles": [{"rate": 1.0, "capacity": 20}],
}

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
# Structure initializers
toolbox.register(
    "individual",
    init_iterate_and_distribute,
    creator.Individual,
    instance=current_instance,
)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("evaluate", eval_routes, instance=current_instance)
# # TODO: add cx fns.
# toolbox.register("mate_1", part_one_edit())
# toolbox.register("mate_2", part_two_edit())
# # TODO: add mutation fns.
# # toolbox.register("mutate_1", tools.mutFlipBit, indpb=0.05)
# toolbox.register(
#     "mutate_swap1", part_one_edit(swap_op, len(current_instance["stores"]))
# )
# toolbox.register(
#     "mutate_inc_dec1", part_one_edit(inc_dec, len(current_instance["stores"]))
# )
# toolbox.register(
#     "mutate_inc_dec2", part_two_edit(inc_dec, len(current_instance["stores"]))
# )
toolbox.register("select", tools.selTournament, tournsize=3)


def main():
    pop = toolbox.population(n=100)

    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # CXPB1  is the probability with which part 1 of two individuals
    #        are crossed
    # CXPB2  is the probability with which part 2 of two individuals
    #        are crossed
    #
    # MUTPB1 is the probability for mutating part 1 of an individual
    # MUTPB2 is the probability for mutating part 2 of an individual
    CXPB1, CXPB2, MUTPB1, MUTPB2 = 0.5, 0.5, 0.2, 0.2

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]
    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    while g < 1000:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # # Apply crossover and mutation on the offspring
        # for child1, child2 in zip(offspring[::2], offspring[1::2]):
        #     if random.random() < CXPB1:
        #         toolbox.mate_1(child1, child2)
        #         if child1.fitness.values:
        #             del child1.fitness.values
        #         if child2.fitness.values:
        #             del child2.fitness.values
        #     if random.random() < CXPB2:
        #         toolbox.mate_2(child1, child2)
        #         if hasattr(child1.fitness, "values"):
        #             del child1.fitness.values
        #         if hasattr(child2.fitness, "values"):
        #             del child2.fitness.values

        # for mutant in offspring:
        #     if random.random() < MUTPB1:
        #         toolbox.mutate_swap1(mutant)
        #         if hasattr(mutant.fitness, "values"):
        #             del mutant.fitness.values
        #     if random.random() < MUTPB2:
        #         toolbox.mutate(mutant)
        #         if hasattr(mutant.fitness, "values"):
        #             del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x * x for x in fits)
        std = abs(sum2 / length - mean ** 2) ** 0.5

        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)


if __name__ == "__main__":
    main()

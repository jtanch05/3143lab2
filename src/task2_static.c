////////////////////////////////////////////////////////////////////////////
// task2_static.c
// -------------------------------------------------------------------------
//
// Finds all primes below n using hybrid Open MPI + OpenMP.
// Built directly from the Lab 1 prime-search algorithm.
// MPI distributes candidate pairs between processes, while OpenMP distributes
// each process's local candidate pairs between threads.
// The root process gathers results with MPI_Gatherv, sorts them, and writes
// the final list to a text file.
//
//////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>

#define OUTPUT_FILE "task2_static_primelist.txt"

// Function prototypes
void read_input(int argc, char *argv[], int my_rank,
                int *n, int *num_threads);
long long count_local_pairs(int n, int my_rank, int p);
void mark_local_primes(int n, int my_rank, int p, long long local_pairs,
                       int *small_primes, int small_count,
                       bool *prime_flags);
int collect_local_primes(int my_rank, int p, long long local_pairs,
                         bool *prime_flags, int **local_primes);
void prepare_gather_data(int n, int p, int *recvCounts, int *displs,
                         int **all_primes, int *total_count);
void print_results(int n, int p, int num_threads, int total_count,
                   double *processTimes, double maxPrepTime,
                   double maxCollectTime, double maxCommTime,
                   double maxOutputTime, double maxOverallTime);
bool is_prime_basic(int k);
bool is_prime_with_list(int k, int *small_primes, int small_count);
int find_primes_basic(int n, int **primes);
int compare_ints(const void *a, const void *b);
void output_primes(int *primes, int count);


int main(int argc, char *argv[])
{
    int my_rank, p;
    int n = 0;
    int num_threads = 1;
    int *small_primes = NULL;
    int small_count;

    double start, end;
    double startBcast, endBcast;
    double startPrep, endPrep;
    double startComp, endComp;
    double startCollect, endCollect;
    double startGather, endGather;
    double startGatherv, endGatherv;
    double startOutput, endOutput;
    double localBcastTime;
    double localPrepTime;
    double localCompTime;
    double localCollectTime;
    double localGatherTime;
    double localGathervTime;
    double localCommTime;
    double localOutputTime = 0.0;
    double overallTime;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);

    // Measure the complete implementation after MPI has been initialised
    start = MPI_Wtime();

    read_input(argc, argv, my_rank, &n, &num_threads);

    // Share input values with all MPI processes
    startBcast = MPI_Wtime();
    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&num_threads, 1, MPI_INT, 0, MPI_COMM_WORLD);
    endBcast = MPI_Wtime();
    localBcastTime = endBcast - startBcast;

    // Preparation phase: configure OpenMP and build local storage
    startPrep = MPI_Wtime();

    omp_set_dynamic(0);
    omp_set_num_threads(num_threads);

    // Same Lab 1 optimisation: build small divisor list up to sqrt(n)
    int sq = (int)sqrt((double)n) + 1;
    small_count = find_primes_basic(sq, &small_primes);

    // MPI cyclic workload distribution
    long long local_pairs = count_local_pairs(n, my_rank, p);

    // Each pair has two possible candidates: 6k-1 and 6k+1
    bool *prime_flags = (bool*)calloc((size_t)((local_pairs > 0) ? local_pairs * 2 : 1), sizeof(bool));

    endPrep = MPI_Wtime();
    localPrepTime = endPrep - startPrep;

    // Hybrid parallel part:
    // MPI has already divided the pairs between processes.
    // OpenMP now divides this process's local pairs between threads.
    startComp = MPI_Wtime();

    mark_local_primes(n, my_rank, p, local_pairs,
                      small_primes, small_count, prime_flags);

    endComp = MPI_Wtime();
    localCompTime = endComp - startComp;

    // Serial local collection phase: convert flags into a result array
    startCollect = MPI_Wtime();

    int *local_primes = NULL;
    int local_count = collect_local_primes(my_rank, p, local_pairs,
                                           prime_flags, &local_primes);

    endCollect = MPI_Wtime();
    localCollectTime = endCollect - startCollect;

    // Gather phase: collect result counts and prime values
    startGather = MPI_Wtime();

    // Gather different local result sizes at root
    int *recvCounts = NULL;
    int *displs = NULL;
    int *all_primes = NULL;
    int total_count = 0;

    if(my_rank == 0)
    {
        recvCounts = (int*)malloc(p * sizeof(int));
        displs = (int*)malloc(p * sizeof(int));
    }

    MPI_Gather(&local_count, 1, MPI_INT,
               recvCounts, 1, MPI_INT,
               0, MPI_COMM_WORLD);

    endGather = MPI_Wtime();
    localGatherTime = endGather - startGather;

    if(my_rank == 0)
        prepare_gather_data(n, p, recvCounts, displs,
                            &all_primes, &total_count);

    startGatherv = MPI_Wtime();

    MPI_Gatherv(local_primes, local_count, MPI_INT,
                all_primes, recvCounts, displs, MPI_INT,
                0, MPI_COMM_WORLD);

    endGatherv = MPI_Wtime();
    localGathervTime = endGatherv - startGatherv;

    localCommTime = localBcastTime
                  + localGatherTime
                  + localGathervTime;

    // Root sorts and writes the final result
    if(my_rank == 0)
    {
        startOutput = MPI_Wtime();
        qsort(all_primes, (size_t)total_count, sizeof(int), compare_ints);
        output_primes(all_primes, total_count);
        endOutput = MPI_Wtime();
        localOutputTime = endOutput - startOutput;
    }

    end = MPI_Wtime();
    overallTime = end - start;

    // Collect process computation times for workload-balance analysis
    double *processTimes = NULL;
    if(my_rank == 0)
        processTimes = (double*)malloc(p * sizeof(double));

    MPI_Gather(&localCompTime, 1, MPI_DOUBLE,
               processTimes, 1, MPI_DOUBLE,
               0, MPI_COMM_WORLD);

    double maxPrepTime;
    double maxCollectTime;
    double maxCommTime;
    double maxOutputTime;
    double maxOverallTime;

    MPI_Reduce(&localPrepTime, &maxPrepTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&localCollectTime, &maxCollectTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&localCommTime, &maxCommTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&localOutputTime, &maxOutputTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&overallTime, &maxOverallTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    if(my_rank == 0)
        print_results(n, p, num_threads, total_count, processTimes,
                      maxPrepTime, maxCollectTime, maxCommTime,
                      maxOutputTime, maxOverallTime);

    free(prime_flags);
    free(small_primes);
    free(local_primes);

    if(my_rank == 0)
    {
        free(recvCounts);
        free(displs);
        free(all_primes);
        free(processTimes);
    }

    MPI_Finalize();
    return 0;
}


// Root process reads and validates n and the number of OpenMP threads.
void read_input(int argc, char *argv[], int my_rank,
                int *n, int *num_threads)
{
    if(my_rank != 0)
        return;

    if(argc != 3)
    {
        printf("Usage: %s <n> <threads-per-process>\n", argv[0]);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    *n = atoi(argv[1]);
    *num_threads = atoi(argv[2]);

    if(*n < 0 || *num_threads < 1)
    {
        printf("n must be non-negative and threads must be at least 1.\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
}


// Counts the cyclic share of candidate pairs assigned to this process.
long long count_local_pairs(int n, int my_rank, int p)
{
    long long local_pairs = 0;

    for(long long pair = my_rank; (5 + 6 * pair) < n; pair += p)
        local_pairs++;

    return local_pairs;
}


// OpenMP threads test this process's local candidate pairs.
void mark_local_primes(int n, int my_rank, int p, long long local_pairs,
                       int *small_primes, int small_count,
                       bool *prime_flags)
{
    #pragma omp parallel for schedule(static) \
        shared(prime_flags, small_primes, small_count, n, p, my_rank, local_pairs)
    for(long long j = 0; j < local_pairs; j++)
    {
        long long pair = my_rank + j * (long long)p;
        int k = (int)(5 + 6 * pair);

        if(is_prime_with_list(k, small_primes, small_count))
            prime_flags[2 * j] = true;

        if(k + 2 < n && is_prime_with_list(k + 2, small_primes, small_count))
            prime_flags[2 * j + 1] = true;
    }
}


// Converts local flags into an array for MPI_Gatherv.
int collect_local_primes(int my_rank, int p, long long local_pairs,
                         bool *prime_flags, int **local_primes)
{
    int local_count = 0;

    for(long long j = 0; j < local_pairs; j++)
        local_count += prime_flags[2 * j] + prime_flags[2 * j + 1];

    *local_primes = (int*)malloc((size_t)((local_count > 0) ? local_count : 1) * sizeof(int));
    int local_index = 0;

    for(long long j = 0; j < local_pairs; j++)
    {
        long long pair = my_rank + j * (long long)p;
        int k = (int)(5 + 6 * pair);

        if(prime_flags[2 * j])
            (*local_primes)[local_index++] = k;
        if(prime_flags[2 * j + 1])
            (*local_primes)[local_index++] = k + 2;
    }

    return local_count;
}


// Root process prepares displacements and storage for MPI_Gatherv.
void prepare_gather_data(int n, int p, int *recvCounts, int *displs,
                         int **all_primes, int *total_count)
{
    *total_count = (n > 2) + (n > 3);
    int offset = *total_count;

    for(int i = 0; i < p; i++)
    {
        displs[i] = offset;
        offset += recvCounts[i];
    }

    *total_count = offset;
    *all_primes = (int*)malloc((size_t)((*total_count > 0) ? *total_count : 1) * sizeof(int));

    int index = 0;
    if(n > 2)
        (*all_primes)[index++] = 2;
    if(n > 3)
        (*all_primes)[index++] = 3;
}


// Root process prints the final result and timing summary.
void print_results(int n, int p, int num_threads, int total_count,
                   double *processTimes, double maxPrepTime,
                   double maxCollectTime, double maxCommTime,
                   double maxOutputTime, double maxOverallTime)
{
    double maxCompTime = processTimes[0];

    printf("\nHybrid Open MPI + OpenMP Prime Search\n");
    printf("n: %d\n", n);
    printf("MPI processes: %d\n", p);
    printf("OpenMP threads per process: %d\n", num_threads);
    printf("Total worker threads: %d\n", p * num_threads);
    printf("Prime numbers found: %d\n", total_count);

    for(int i = 0; i < p; i++)
    {
        printf("Process %d computation time: %lf seconds\n", i, processTimes[i]);
        if(processTimes[i] > maxCompTime)
            maxCompTime = processTimes[i];
    }

    printf("Preparation time (max process): %lf seconds\n", maxPrepTime);
    printf("Parallel computation time (max process): %lf seconds\n", maxCompTime);
    printf("Local result collection time (max process): %lf seconds\n", maxCollectTime);
    printf("MPI communication time (broadcast + gather + gatherv, max process): %lf seconds\n", maxCommTime);
    printf("Sorting and output time: %lf seconds\n", maxOutputTime);
    printf("Overall time (including MPI communication, sorting and output): %lf seconds\n", maxOverallTime);
    printf("Primes written to %s\n", OUTPUT_FILE);
}


// Tests whether k is prime using trial division on 6k+-1 divisors only.
bool is_prime_basic(int k)
{
    for(int i = 5; (long long)i * i <= k; i += 6)
    {
        if(k % i == 0 || k % (i + 2) == 0)
            return false;
    }
    return true;
}


// Tests whether k is prime by dividing only by known small primes.
bool is_prime_with_list(int k, int *small_primes, int small_count)
{
    for(int idx = 0; idx < small_count; idx++)
    {
        int p = small_primes[idx];
        if((long long)p * p > k)
            break;
        if(k % p == 0)
            return false;
    }
    return true;
}


// Lab 1 serial helper: finds all primes strictly less than n.
int find_primes_basic(int n, int **primes)
{
    int capacity = (n > 2) ? n / 2 : 1;
    int *result = (int*)malloc((size_t)capacity * sizeof(int));
    int count = 0;

    if(n > 2)
        result[count++] = 2;
    if(n > 3)
        result[count++] = 3;

    for(int k = 5; k < n; k += 6)
    {
        if(is_prime_basic(k))
            result[count++] = k;
        if(k + 2 < n && is_prime_basic(k + 2))
            result[count++] = k + 2;
    }

    *primes = result;
    return count;
}


// qsort comparison function
int compare_ints(const void *a, const void *b)
{
    int num1 = *((const int*)a);
    int num2 = *((const int*)b);
    return (num1 > num2) - (num1 < num2);
}


// Root process writes the sorted prime list to file
void output_primes(int *primes, int count)
{
    FILE *fp = fopen(OUTPUT_FILE, "w");

    for(int i = 0; i < count; i++)
        fprintf(fp, "%d\n", primes[i]);

    fclose(fp);
}

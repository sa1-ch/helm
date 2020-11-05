import os
import pickle
from pathlib import Path

from metaflow import (FlowSpec, IncludeFile, batch, conda, conda_base,
                      resources, step)

from utils import conditionally


def get_python_version():
    """
    A convenience function to get the python version used to run this
    tutorial. This ensures that the conda environment is created with an
    available version of python.

    """
    import platform

    versions = {"2": "2.7.15", "3": "3.7.3"}
    return versions[platform.python_version_tuple()[0]]


def script_path(filename):
    """
    A convenience function to get the absolute path to a file in this
    tutorial's directory. This allows the tutorial to be launched from any
    directory.

    """
    import os

    filepath = os.path.join(os.path.dirname(__file__))
    return os.path.join(filepath, filename)


class MovieStatsFlow(FlowSpec):
    """
    A flow to generate some statistics about the movie genres.

    The flow performs the following steps:
    1) Ingests a CSV into a Pandas Dataframe.
    2) Fan-out over genre using Metaflow foreach.
    3) Compute quartiles for each genre.
    4) Save a dictionary of genre specific statistics.

    """

    movie_data = IncludeFile(
        "movie_data",
        help="The path to a movie metadata file.",
        default=script_path("movies.csv"),
    )

    @step
    def start(self):

        """
        The start step:
        1) Loads the movie metadata into pandas dataframe.
        2) Finds all the unique genres.
        3) Launches parallel statistics computation for each genre.

        """
        from io import StringIO

        import pandas

        # Load the data set into a pandas dataframe.
        self.dataframe = pandas.read_csv(StringIO(self.movie_data))

        # The column 'genres' has a list of genres for each movie. Let's get
        # all the unique genres.
        self.genres = {
            genre for genres in self.dataframe["genres"] for genre in genres.split("|")
        }
        self.genres = list(self.genres)
        self.next(self.start_local, self.start_batch)

    @step
    def start_local(self):
        """
        The start step:
        1) Launches parallel statistics computation for each genre.
    
        """

        print("Starting local")
        # We want to compute some statistics for each genre. The 'foreach'
        # keyword argument allows us to compute the statistics for each genre in
        # parallel (i.e. a fan-out).
        self.next(self.compute_statistics_local, foreach="genres")

    @conditionally(batch(cpu=2, memory=500), os.environ.get("RUN_BATCH") == "y")
    @step
    def start_batch(self):
        """
        The start step:
        1) Launches parallel statistics computation for each genre.

        """

        print("Starting batch")
        # We want to compute some statistics for each genre. The 'foreach'
        # keyword argument allows us to compute the statistics for each genre in
        # parallel (i.e. a fan-out).
        self.next(self.compute_statistics_batch, foreach="genres")

    @resources(memory=500, cpu=1)
    @step
    def compute_statistics_local(self):
        """
        Compute statistics for a single genre.

        """
        # The genre currently being processed is a class property called
        # 'input'.
        self.genre = self.input
        print("Computing statistics for %s" % self.genre)

        # if self.genre == "Biography":
        #     raise RuntimeError("Failing!")

        # Find all the movies that have this genre and build a dataframe with
        # just those movies and just the columns of interest.
        selector = self.dataframe["genres"].apply(lambda row: self.genre in row)
        self.dataframe = self.dataframe[selector]
        self.dataframe = self.dataframe[["movie_title", "genres", "gross"]]

        # Get some statistics on the gross box office for these titles.
        points = [0.25, 0.5, 0.75]
        self.quartiles = self.dataframe["gross"].quantile(points).values

        # Join the results from other genres.
        self.next(self.join_local)

    # @batch(memory=500, cpu=1)
    @step
    def compute_statistics_batch(self):
        """
        Compute statistics for a single genre.

        """
        # The genre currently being processed is a class property called
        # 'input'.
        self.genre = self.input
        print("Computing statistics for %s" % self.genre)

        # if self.genre == "Biography":
        #     raise RuntimeError("Failing!")

        # Find all the movies that have this genre and build a dataframe with
        # just those movies and just the columns of interest.
        selector = self.dataframe["genres"].apply(lambda row: self.genre in row)
        self.dataframe = self.dataframe[selector]
        self.dataframe = self.dataframe[["movie_title", "genres", "gross"]]

        # Get some statistics on the gross box office for these titles.
        points = [0.25, 0.5, 0.75]
        self.quartiles = self.dataframe["gross"].quantile(points).values

        # Join the results from other genres.
        self.next(self.join_batch)

    @step
    def join_local(self, inputs):
        """
        Join our parallel branches and merge results into a dictionary.

        """
        # Merge results from the genre specific computations.
        self.genre_stats_local = {
            inp.genre.lower(): {"quartiles": inp.quartiles, "dataframe": inp.dataframe}
            for inp in inputs
        }

        self.next(self.write_outputs)

    @step
    def join_batch(self, inputs):
        """
        Join our parallel branches and merge results into a dictionary.

        """

        # Merge results from the genre specific computations.
        self.genre_stats_batch = {
            inp.genre.lower(): {"quartiles": inp.quartiles, "dataframe": inp.dataframe}
            for inp in inputs
        }

        self.next(self.write_outputs)

    @step
    def write_outputs(self, inputs):
        """
        Join our parallel branches and merge results into a dictionary.

        """

        self.merge_artifacts(inputs)

        Path("outputs/").mkdir(exist_ok=True)
        with open('outputs/genre_stats_batch.pkl', 'wb') as batch_file:
            pickle.dump(self.genre_stats_batch, batch_file, protocol=pickle.HIGHEST_PROTOCOL)

        with open('outputs/genre_stats_local.pkl', 'wb') as local_file:
            pickle.dump(self.genre_stats_local, local_file, protocol=pickle.HIGHEST_PROTOCOL)

        self.next(self.end)

    @step
    def end(self):
        """
        End the flow.

        """
        print("Completed")


if __name__ == "__main__":
    MovieStatsFlow()

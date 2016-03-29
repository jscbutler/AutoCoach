using System;
using System.Globalization;
using BusinessObjects;
using Public;
using TrainingPeaksConnection;
using WorkoutCalculator;

namespace TestConsoleRunner
{
    internal class Program
    {
        private static void Main(string[] args)
        {
            var athlete = new Athlete
            {
                TPData = new TrainingPeaksAthleteData
                {
                    LoginName = "jscbutler",
                    LoginPassword = "xcelite1",
                    AccountType = TrainingPeaksAthleteAccountTypes.SelfCoachedPremium
                },
                FTBikePower = 260,
                WeightKilos = 86.3
            };
            Console.Out.WriteLine("Starting connection to TrainingPeaks....");

            var conn = new TrainingPeaksClient();
            Console.Out.WriteLine("Initialised SOAP Client - starting to request Person Data");
            conn.GetAthleteData(athlete);
            Console.Out.WriteLine("Received Person Data - " + athlete.TPData.AthleteName + " ID:" +
                                  athlete.TPData.PersonID);
            Console.Out.WriteLine("Accesing last workout for " + athlete.TPData.AthleteName);
            //var workout = conn.GetLastWorkoutIn30Days(athlete);
            //pwx pwxData = conn.GetExtendedWorkoutData(athlete, workout);
            var fromDate = DateTime.ParseExact("20/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture);
            var toDate = DateTime.ParseExact("30/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture);
            var workouts = conn.GetAllWorkoutsInDateRange(athlete, fromDate,toDate);
            foreach (var workout in workouts)
            {
                if (workout.SportType == SportType.Bike)
                {
                    var pwxData = conn.GetExtendedWorkoutData(athlete, workout);
                    var extractor = new PWXDataExtractor(pwxData);
                    var workoutSamples = extractor.ExtractData();
                    var calculator = new WorkoutSamplesCalculator(workoutSamples, athlete);
                    Console.Out.WriteLine(workout.SportType + " on " + workout.StartDate + " TSS: " + workoutSamples.SummaryTrainingStressScore + " Duration: " + workout.Duration);
                    var cadenceRanges = calculator.ClassifyWorkoutCadenceRanges();
                    foreach (var cadenceRange in cadenceRanges)
                    {
                        Console.WriteLine(cadenceRange);
                    }
                    Console.WriteLine("==========================================");
                }
            }

            Console.In.ReadLine();
        }
    }
}
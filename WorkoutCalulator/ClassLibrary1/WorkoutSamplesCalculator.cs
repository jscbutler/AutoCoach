using System;
using System.Collections.Generic;
using System.Linq;
using BusinessObjects;
using Public;

namespace WorkoutCalculator
{
    public class WorkoutSamplesCalculator
    {
        private readonly IList<CadenceRange> _cadenceRanges = new List<CadenceRange>(5);
        public readonly IList<EnergySystemRange> _powerEnergyRanges = new List<EnergySystemRange>(6);
        public readonly IList<EnergySystemRange> _heartRateEnergyRanges = new List<EnergySystemRange>(6);

        private readonly WorkoutSamples workoutSamples;
        private double _intensityFactor = double.NaN;
        private double _normalizedPower = double.NaN;
        private double _trainingStrssScorePower = double.NaN;

        public WorkoutSamplesCalculator(WorkoutSamples woSamples)
        {
            workoutSamples = woSamples;
            // Can externally define these ranges later.
            _cadenceRanges.Add(new CadenceRange(0, 40, WorkoutCadenceFocus.None));
            _cadenceRanges.Add(new CadenceRange(40, 65, WorkoutCadenceFocus.Grinding));
            _cadenceRanges.Add(new CadenceRange(65, 80, WorkoutCadenceFocus.Climbing));
            _cadenceRanges.Add(new CadenceRange(80, 100, WorkoutCadenceFocus.Normal));
            _cadenceRanges.Add(new CadenceRange(100, 250, WorkoutCadenceFocus.Spinning));

            _powerEnergyRanges.Add(new EnergySystemRange(0,55,WorkoutEnergySystemFocus.Zone1));
            _powerEnergyRanges.Add(new EnergySystemRange(55, 75, WorkoutEnergySystemFocus.Zone2));
            _powerEnergyRanges.Add(new EnergySystemRange(75, 90, WorkoutEnergySystemFocus.Zone3));
            _powerEnergyRanges.Add(new EnergySystemRange(90, 105, WorkoutEnergySystemFocus.Zone4));
            _powerEnergyRanges.Add(new EnergySystemRange(105, 120, WorkoutEnergySystemFocus.Zone5));
            _powerEnergyRanges.Add(new EnergySystemRange(120, 10000, WorkoutEnergySystemFocus.Zone6));

            _heartRateEnergyRanges.Add(new EnergySystemRange(0, 81, WorkoutEnergySystemFocus.Zone1));
            _heartRateEnergyRanges.Add(new EnergySystemRange(81, 89, WorkoutEnergySystemFocus.Zone2));
            _heartRateEnergyRanges.Add(new EnergySystemRange(90, 94, WorkoutEnergySystemFocus.Zone3));
            _heartRateEnergyRanges.Add(new EnergySystemRange(94, 103, WorkoutEnergySystemFocus.Zone4));
            _heartRateEnergyRanges.Add(new EnergySystemRange(103, 105, WorkoutEnergySystemFocus.Zone5));
            _heartRateEnergyRanges.Add(new EnergySystemRange(105, 10000, WorkoutEnergySystemFocus.Zone6));

            // Run Pace
            //        Zone 1 Slower than 129% of FTP
            //Zone 2 114% to 129% of FTP
            //Zone 3 106% to 113% of FTP
            //Zone 4 99% to 105% of FTP
            //Zone 5a 97% to 100% of FTP
            //Zone 5b 90% to 96% of FTP
            //Zone 5c Faster than 90% of FTP           

        }

        public double GetAveragePower()
        {
            return CalculateVectorAverage(workoutSamples.PowerVector);
        }

        public double GetNormalizedPower()
        {
            _normalizedPower = CalculateVectorNormalizedAverage(workoutSamples.PowerVector);
            return _normalizedPower;
        }

        public double GetAverageCadence()
        {
            return CalculateVectorAverage(workoutSamples.CadenceVector);
        }

        public double GetAverageHeartRate()
        {
            return CalculateVectorAverage(workoutSamples.HeartRateVector);
        }

        public double GetAverageSpeed()
        {
            return CalculateVectorAverage(workoutSamples.SpeedVector);
        }

        internal double CalculateVectorAverage(WorkoutSampleVector vector)
        {
            if (!vector.HasData)
                return 0;
            var weightedCumulative = vector.Vector[0].dataPoint;

            for (var i = 1; i < vector.NumberOfSamples; i++)
            {
                if (vector.Vector[i].dataPoint <= 0) continue;
                var timeDiff = vector.Vector[i].timeOffsetSeconds - vector.Vector[i - 1].timeOffsetSeconds;
                weightedCumulative = weightedCumulative + timeDiff*vector.Vector[i].dataPoint;
            }
            var divisor = vector.Vector[vector.NumberOfSamples - 1].timeOffsetSeconds;

            var average = weightedCumulative/divisor;
            return Math.Round(average);
        }

        public double CalculateNonZeroVectorAverage(WorkoutSampleVector vector)
        {
            if (!vector.HasData)
                return 0;

            var weightedCumulative = vector.Vector[0].dataPoint > 0 ? vector.Vector[0].dataPoint : 0;
            double divisor = 1;
            for (var i = 1; i < vector.NumberOfSamples; i++)
            {
                if (vector.Vector[i].dataPoint <= 0)
                    continue;
                var timeDiff = vector.Vector[i].timeOffsetSeconds - vector.Vector[i - 1].timeOffsetSeconds;
                weightedCumulative = weightedCumulative + timeDiff*vector.Vector[i].dataPoint;
                divisor += timeDiff;
            }
            var average = weightedCumulative/divisor;
            return Math.Round(average);
        }

        public double CalculateVectorNormalizedAverage(WorkoutSampleVector vector)
        {
            if (!vector.HasData)
                return 0;
            if (vector.NumberOfSamples < 30)
                return CalculateVectorAverage(vector);

            var movingAverageBuffer = new SimpleMovingAverage(30);
            double movingAverage = 0;
            var movingAverageSamples = 1;

            movingAverageBuffer.Add(vector.Vector[0].dataPoint);

            for (var i = 1; i < vector.NumberOfSamples; i++)
            {
                if (vector.Vector[i].dataPoint < 0)continue;
                var timeDiff = vector.Vector[i].timeOffsetSeconds - vector.Vector[i - 1].timeOffsetSeconds;
                for (var j = 0; j < timeDiff; j++)
                    //Cannot multiply value across time in the sample as we need a 30s moving avg.
                {
                    movingAverageBuffer.Add(vector.Vector[i].dataPoint);
                    if (movingAverageBuffer.NumberOfSamples >= 30)
                    {
                        movingAverage += Math.Pow(Math.Round(movingAverageBuffer.Average()), 4);
                        movingAverageSamples++;
                    }
                }
            }
            var average = movingAverage/movingAverageSamples;
            average = Math.Round(Math.Pow(average, 0.25));
            return average;
        }

        public double CalcualteIntensityFactor(double ftPower)
        {
            if (double.IsNaN(_normalizedPower))
                _normalizedPower = CalculateVectorNormalizedAverage(workoutSamples.PowerVector);
            _intensityFactor = Math.Round(_normalizedPower/ftPower, 2);
            return _intensityFactor;
        }

        public double Calculate_Power_TrainingStressScore(double ftPower)
        {
            //TSS = (sec x NP x _intensityFactor)/ (FTP x 3600) x 100
            var sec =
                workoutSamples.PowerVector.Vector[workoutSamples.PowerVector.NumberOfSamples - 1].timeOffsetSeconds;
            if (double.IsNaN(_normalizedPower))
                _normalizedPower = CalculateVectorNormalizedAverage(workoutSamples.PowerVector);
            if (double.IsNaN(_intensityFactor))
                _intensityFactor = CalcualteIntensityFactor(ftPower);
            var numerator = sec*_normalizedPower*0.96;
            var denominator = ftPower*3600;
            _trainingStrssScorePower = numerator/denominator*100;
            return _trainingStrssScorePower;
        }

        public IList<CadenceRange>  ClassifyWorkoutCadenceRanges()
        {
            ClassifyWorkoutCadenceType(_cadenceRanges, workoutSamples.CadenceVector, 0);
            return _cadenceRanges;
        }

        public IList<EnergySystemRange> ClassifyWorkoutPowerRanges(double ftPower)
        {
            ClassifyWorkoutCadenceType(_powerEnergyRanges, workoutSamples.PowerVector, ftPower);
            return _powerEnergyRanges;
        }
        public IList<EnergySystemRange> ClassifyWorkoutEnergeRangesFromHeartRate(double thresholdHeartRate)
        {
            ClassifyWorkoutCadenceType(_heartRateEnergyRanges, workoutSamples.HeartRateVector, thresholdHeartRate);
            return _heartRateEnergyRanges;
        }

        internal IEnumerable<Range> ClassifyWorkoutCadenceType( IEnumerable<Range> ranges,  WorkoutSampleVector vector, double referenceValue)
        {
         
            if (vector.NumberOfSamples < 2)
                return ranges;
            var rangeList = ranges as IList<Range> ?? ranges.ToList();
            ClassifyCadenceDataPoint(vector.Vector[0].dataPoint, rangeList, referenceValue);
            for (var i = 1; i < vector.NumberOfSamples; i++)
            {
                if (!(vector.Vector[i].dataPoint >= 0)) continue;
                var timeDiff = vector.Vector[i].timeOffsetSeconds -
                               vector.Vector[i - 1].timeOffsetSeconds;
                for (var j = 0; j < timeDiff; j++)
                {
                    ClassifyCadenceDataPoint(vector.Vector[i].dataPoint, rangeList, referenceValue);
                }
            }
            var totalSamples = rangeList.Sum(range => range.QuanityOfSamples);
            foreach (var range in rangeList)
            {
                var percent = range.QuanityOfSamples/(double) totalSamples*100;
                range.PercentOfTotal = Math.Round(percent);
            }
            return rangeList;
        }

        internal void ClassifyCadenceDataPoint(double dataPoint, IList<Range> ranges , double referenceValue)
        {
            if (referenceValue > 0)
                dataPoint = (dataPoint/referenceValue)*100; // data as a percentage of the reference.
            foreach (var range in ranges)
            {
                if ((dataPoint > range.MinValue) && (dataPoint <= range.MaxValue))
                {

                    range.QuanityOfSamples++;
                    break;
                }
            }
        }
    }
}
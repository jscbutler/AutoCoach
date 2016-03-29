using System;
using System.Collections.Generic;
using System.Linq;
using BusinessObjects;
using Public;
using static System.Double;

namespace WorkoutCalculator
{
    public class WorkoutSamplesCalculator
    {
        private readonly WorkoutSamples _workoutSamples;
        private double _intensityFactor = NaN;
        private double _normalizedPower = NaN;
        private readonly IAthlete _athlete;

        public WorkoutSamplesCalculator(WorkoutSamples woSamples, IAthlete athlete)
        {
            _workoutSamples = woSamples;
            _athlete = athlete;
        }

        public double GetAveragePower()
        {
            return CalculateVectorAverage(_workoutSamples.PowerVector);
        }

        public double GetNormalizedPower()
        {
            _normalizedPower = CalculateVectorNormalizedAverage(_workoutSamples.PowerVector);
            return _normalizedPower;
        }

        public double GetAverageCadence()
        {
            return CalculateVectorAverage(_workoutSamples.CadenceVector);
        }

        public double GetAverageHeartRate()
        {
            return CalculateVectorAverage(_workoutSamples.HeartRateVector);
        }

        public double GetAverageSpeed()
        {
            return CalculateVectorAverage(_workoutSamples.SpeedVector);
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

        public double CalcualteIntensityFactor()
        {
            if (IsNaN(_normalizedPower))
                _normalizedPower = CalculateVectorNormalizedAverage(_workoutSamples.PowerVector);
            CalcIf();
            return _intensityFactor;
        }

        private void CalcIf()
        {
            _intensityFactor = Math.Round(_normalizedPower / _athlete.FTBikePower, 2);
        }

        public double Calculate_Power_TrainingStressScore(double ftPower)
        {
            //TSS = (sec x NP x _intensityFactor)/ (FTP x 3600) x 100
            if (_workoutSamples != null)
            {
                var sec =
                    _workoutSamples.PowerVector.Vector[_workoutSamples.PowerVector.NumberOfSamples - 1].timeOffsetSeconds;
                if (IsNaN(_normalizedPower))
                    _normalizedPower = CalculateVectorNormalizedAverage(_workoutSamples.PowerVector);
                if (IsNaN(_intensityFactor))
                    _intensityFactor = CalcualteIntensityFactor();
                var numerator = sec*_normalizedPower*0.96;
                var denominator = ftPower*3600;
                return numerator/denominator*100;
            }
            return 0;
        }

        public IList<ICadenceRange>  ClassifyWorkoutCadenceRanges()
        {
            ClassifyWorkoutCadenceType(
                _athlete.BikeCadenceRanges, _workoutSamples.CadenceVector, 0);
            return _athlete.BikeCadenceRanges;
        }

        public IList<IEnergySystemRange> ClassifyWorkoutPowerRanges(double ftPower)
        {
            ClassifyWorkoutCadenceType(_athlete.BikePowerEnergyRanges, _workoutSamples.PowerVector, ftPower);
            return _athlete.BikePowerEnergyRanges;
        }
        public IList<IEnergySystemRange> ClassifyWorkoutEnergeRangesFromHeartRate(double thresholdHeartRate)
        {
            ClassifyWorkoutCadenceType(_athlete.BikeHeartRateEnergyRanges, _workoutSamples.HeartRateVector, thresholdHeartRate);
            return _athlete.BikeHeartRateEnergyRanges;
        }

        internal IEnumerable<IRange> ClassifyWorkoutCadenceType( IEnumerable<IRange> ranges,  WorkoutSampleVector vector, double referenceValue)
        {
         
            if (vector.NumberOfSamples < 2)
                return ranges;
            var rangeList = ranges as IList<IRange> ?? ranges.ToList();
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

        internal void ClassifyCadenceDataPoint(double dataPoint, IList<IRange> ranges , double referenceValue)
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
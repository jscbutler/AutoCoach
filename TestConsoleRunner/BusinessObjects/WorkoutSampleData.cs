using System;
using System.Runtime.InteropServices;
using Public;

namespace BusinessObjects
{
    public enum WorkoutSampleDataType
    {
        Power = 0,
        Cadence,
        HeartRate,
        Speed
    }

    [StructLayout(LayoutKind.Explicit)]
    public struct SampleDataPoint
    {
        [FieldOffset(0)] public double timeOffsetSeconds;
        [FieldOffset(8)] public double dataPoint;

        public override string ToString()
        {
            return "TimeOffset:" + timeOffsetSeconds + " DataPoint:" + dataPoint;
        }
    }

    public class Range
    {
        public readonly int MaxValue;
        public readonly int MinValue;
        public int QuanityOfSamples;
        public double PercentOfTotal;
        public Range(int min, int max)
        {
            MinValue = min;
            MaxValue = max;
            QuanityOfSamples = 0;
            PercentOfTotal = 0;
        }

        public override string ToString()
        {
            return " Samples:" + QuanityOfSamples + " PercentOtTotal:" + PercentOfTotal + "%";
        }
    }

    public class CadenceRange : Range
    {
        
        public readonly WorkoutCadenceFocus RangeFocus;
       public CadenceRange(int min, int max, WorkoutCadenceFocus rangeFocus)
            : base(min, max)
        {            
            RangeFocus = rangeFocus;
        }
        public override string ToString()
        {
            return "RangeFocus:" + RangeFocus + base.ToString();
        }

    }
    public class EnergySystemRange : Range
    {
        public readonly WorkoutEnergySystemFocus EnergySystemFocus;
        public EnergySystemRange(int min, int max, WorkoutEnergySystemFocus rangeFocus)
            : base (min,max)
        {            
            EnergySystemFocus = rangeFocus;
        }
        public override string ToString()
        {
            return "EnergySystemRangeFocus:" + EnergySystemFocus + base.ToString();
        }

    }

    public class WorkoutSampleVector
    {
        public WorkoutSampleVector(int numberOfSamples, WorkoutSampleDataType dataType)
        {
            NumberOfSamples = numberOfSamples;
            SampleDataType = dataType;
            Vector = new SampleDataPoint[numberOfSamples];
        }

        public bool HasData { get; private set; }

        public SampleDataPoint[] Vector { get; }
        public int NumberOfSamples { get; }
        public int NextPointIndex { get; private set; }

        public WorkoutSampleDataType SampleDataType { get; private set; }

        public void AddPoint(double timeoffset, double data)
        {
            if (NextPointIndex >= NumberOfSamples)
                throw new IndexOutOfRangeException("Adding more Samples than allocated");
            Vector[NextPointIndex].dataPoint = data;
            Vector[NextPointIndex].timeOffsetSeconds = timeoffset;
            NextPointIndex++;
            HasData = true;
        }
    }

    public class WorkoutSamples
    {
        public WorkoutSamples(int numberOfSamples)
        {
            CadenceVector = new WorkoutSampleVector(numberOfSamples, WorkoutSampleDataType.Cadence);
            HeartRateVector = new WorkoutSampleVector(numberOfSamples, WorkoutSampleDataType.HeartRate);
            PowerVector = new WorkoutSampleVector(numberOfSamples, WorkoutSampleDataType.Power);
            SpeedVector = new WorkoutSampleVector(numberOfSamples, WorkoutSampleDataType.Speed);
        }

        public WorkoutSampleVector PowerVector { get; set; }
        public WorkoutSampleVector CadenceVector { get; set; }
        public WorkoutSampleVector HeartRateVector { get; set; }
        public WorkoutSampleVector SpeedVector { get; set; }

        public double SummaryTrainingStressScore{get;set;}
        public double SummaryWork { get; set; }
        public double SummaryDuration { get; set; }

        public void AddPoint(double timeoffset, double data, WorkoutSampleDataType dataType)
        {
            switch (dataType)
            {
                case WorkoutSampleDataType.Power:
                    PowerVector.AddPoint(timeoffset, data);
                    break;
                case WorkoutSampleDataType.Cadence:
                    CadenceVector.AddPoint(timeoffset, data);
                    break;
                case WorkoutSampleDataType.HeartRate:
                    HeartRateVector.AddPoint(timeoffset, data);
                    break;
                case WorkoutSampleDataType.Speed:
                    SpeedVector.AddPoint(timeoffset, data);
                    break;
            }
        }
    }
}
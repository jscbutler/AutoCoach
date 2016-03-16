using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BusinessObjects
{
    public class SimpleMovingAverage
    {
        private readonly double[] buffer;
        int _nextFree;
        private readonly int _length;
        private double _total;
        public int NumberOfSamples { get; private set; }

        public SimpleMovingAverage(int length)
        {
            if (length <= 0)
                throw new IndexOutOfRangeException("Cannot specify a zero length SimpleMovingAverage Buffer length");
            _length = length;
            buffer = new double[_length];
            _nextFree = 0;
        }

        public void Add(double dataPoint)
        {        
            if (NumberOfSamples >= _length)
            {
                _total -= buffer[_nextFree];
            }
            buffer[_nextFree] = dataPoint;
            _total += dataPoint;
            _nextFree = (_nextFree + 1)%_length;
            NumberOfSamples++;
        }

        public double Average()
        {
            if (NumberOfSamples < _length)
                return _total/NumberOfSamples;
            return _total/_length;
        }
    }
}

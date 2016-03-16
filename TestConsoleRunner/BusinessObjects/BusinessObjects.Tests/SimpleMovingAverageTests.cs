using System;
using Xunit;

namespace BusinessObjects.Tests
{
    
    public class SimpleMovingAverageTests
    {
        [Fact]
        public void TestZeroLengthInstance()
        {
            Assert.Throws<IndexOutOfRangeException> (() =>  new SimpleMovingAverage(0));
        }

        [Fact]
        public void TestSimpleNotFullStaticAverage()
        {
            var sma = new SimpleMovingAverage(5);
            sma.Add(3);
            sma.Add(4);
            sma.Add(2);
            sma.Add(3);
            var average = sma.Average();
            Assert.Equal(3, average);
        }
        [Fact]
        public void TestSimpleFullStaticAverage()
        {
            var sma = new SimpleMovingAverage(5);
            sma.Add(3);
            sma.Add(4);
            sma.Add(2);
            sma.Add(3);
            sma.Add(3);
            var average = sma.Average();
            Assert.Equal(3, average);
        }

        [Fact]
        public void TestSimpleMovingAverage()
        {
            var sma = new SimpleMovingAverage(5);
            sma.Add(10);
            sma.Add(55);
            sma.Add(33);    
            sma.Add(56);
            sma.Add (88);
            sma.Add(23);
            var average = sma.Average();
            Assert.Equal(51, average);
        }

    }
}

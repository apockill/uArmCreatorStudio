#pragma once
/*  linreg.h
Linear Regression calculation class

by: David C. Swaim II, Ph.D.

This class implements a standard linear regression on
experimental data using a least squares fit to a straight
line graph.  Calculates coefficients a and b of the equation:

y = a + b * x

for data points of x and y.  Also calculates the coefficient of
determination, the coefficient of correlation, and standard
error of estimate.

The value n (number of points) must be greater than 2 to
calculate the regression.  This is primarily because the
standard error has a (N-2) in the denominator.

Check haveData() to see if there is enough data in
LinearRegression to get values.

You can think of the x,y pairs as 2 dimensional points.
The class Point2D is included to allow pairing x and y
values together to represent a point on a plane.

*/

#ifndef _LINREG_H_
#define _LINREG_H_




class LinearRegression
{
	

public:
	// Constructor using an array of Point2D objects
	// This is also the default constructor

	// Constructor using arrays of x values and y values
	LinearRegression(double *x, double *y, long size = 0);

	virtual void addXY(const double& x, const double& y);

	// Must have at least 3 points to calculate
	// standard error of estimate.  Do we have enough data?
	int haveData() const { return (n > 2 ? 1 : 0); }
	long items() const { return n; }

	virtual double getA() const { return a; }
	virtual double getB() const { return b; }

	double getCoefDeterm() const { return coefD; }
	double getCoefCorrel() const { return coefC; }
	double getStdErrorEst() const { return stdError; }
	virtual double estimateY(double x) const { return (a + b * x); }

protected:
	long n;             // number of data points input so far
	double sumX, sumY;  // sums of x and y
	double sumXsquared, // sum of x squares
		sumYsquared; // sum y squares
	double sumXY;       // sum of x*y

	double a, b;        // coefficients of f(x) = a + b*x
	double coefD,       // coefficient of determination
		coefC,       // coefficient of correlation
		stdError;    // standard error of estimate

	void Calculate();   // calculate coefficients
};

#endif                      // end of linreg.h
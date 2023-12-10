pub fn multiply<T>(a: T, b: T, c: T) -> T
where
    T: std::ops::Mul<Output = T> + Copy,
{
    a * b * c
}


use simple_multiply::multiply;

fn main() {
    let result = multiply(2, 3, 4);
    println!("Result: {}", result);

    // 他の型でも試してみる
    let result_float = multiply(1.5, 2.5, 3.0);
    println!("Result (float): {}", result_float);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_multiply_integers() {
        let result = multiply(2, 3, 4);
        assert_eq!(result, 24);
    }

    #[test]
    fn test_multiply_floats() {
        let result = multiply(1.5, 2.5, 3.0);
        assert_eq!(result, 11.25);
    }
}

// java -cp "C:\Users\yoshi\tmp\commons-lang3-3.20.0\commons-lang3-3.20.0.jar" ReferenceNonJDKClass.java
import org.apache.commons.lang3.RandomUtils;

public class ReferenceNonJDKClass {
    public static void main(String[] args) {
        IO.println(RandomUtils.nextInt());
    }
}
